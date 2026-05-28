"""
Cross-platform daemonise / PID file helpers.
- Unix: double-fork daemon.
- Windows: subprocess detach via creationflags.
- PID file under ~/.shredcli/shred.pid
- Logging to ~/.shredcli/shred.log
"""

from __future__ import annotations

import atexit
import os
import platform
import signal
import sys
import time
from pathlib import Path
from typing import Callable, Optional

# Constants
DATA_DIR = Path.home() / ".shredcli"
PID_FILE = DATA_DIR / "shred.pid"
LOG_FILE = DATA_DIR / "shred.log"
STATUS_FILE = DATA_DIR / "status.json"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_pid() -> Optional[int]:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except Exception:
        return None


def write_pid(pid: int) -> None:
    ensure_dirs()
    PID_FILE.write_text(str(pid))


def remove_pid() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def write_status(data: dict) -> None:
    """Write status dict to JSON file."""
    import json

    ensure_dirs()
    try:
        STATUS_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def read_status() -> dict:
    """Read status dict from JSON file."""
    import json

    if not STATUS_FILE.exists():
        return {}
    try:
        return json.loads(STATUS_FILE.read_text())
    except Exception:
        return {}


def _setup_logging() -> None:
    import logging
    ensure_dirs()
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class DaemonRunner:
    """
    Manage the background daemon lifecycle.
    """

    def __init__(
        self,
        main_func: Callable[[], None],
        on_sigterm: Optional[Callable[[], None]] = None,
    ) -> None:
        self.main_func = main_func
        self.on_sigterm = on_sigterm
        self._stopped = False

    def _register_cleanup(self) -> None:
        atexit.register(remove_pid)

    def _sigterm_handler(self, signum, frame) -> None:  # noqa: U100
        import json

        self._stopped = True
        if self.on_sigterm:
            try:
                self.on_sigterm()
            except Exception:
                pass
        remove_pid()
        try:
            STATUS_FILE.write_text(json.dumps({"running": False}))
        except Exception:
            pass
        sys.exit(0)

    def _daemonize_unix(self) -> None:
        try:
            pid = os.fork()
            if pid > 0:
                # Parent exits
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, "r")
        so = open(os.devnull, "a+")
        se = open(os.devnull, "a+")
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def _run_in_foreground(self) -> None:
        _setup_logging()
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        signal.signal(signal.SIGINT, self._sigterm_handler)
        write_pid(os.getpid())
        self._register_cleanup()
        self.main_func()

    def _run_daemon_unix(self) -> int:
        """Double-fork to create a proper Unix daemon. Returns child PID to parent."""
        # First fork - parent returns, child continues
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process: wait for child to write PID file
                time.sleep(0.5)
                child_pid = read_pid()
                if child_pid and child_pid != pid:
                    return child_pid
                return pid
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)

        # First child: decouple from parent environment
        os.chdir("/")
        os.setsid()  # Create new session
        os.umask(0)

        # Second fork - prevent acquiring controlling terminal
        try:
            pid = os.fork()
            if pid > 0:
                # First child exits
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)

        # Grandchild (actual daemon process)
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Redirect standard file descriptors to /dev/null
        try:
            si = open(os.devnull, "r")
            so = open(os.devnull, "a+")
            se = open(os.devnull, "a+")
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())
            si.close()
            so.close()
            se.close()
        except Exception:
            pass

        _setup_logging()
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        signal.signal(signal.SIGINT, self._sigterm_handler)
        write_pid(os.getpid())
        self._register_cleanup()
        self.main_func()
        return os.getpid()

    def start(self, daemonize: bool = True) -> Optional[int]:
        """
        Start the daemon. If daemonize=False, run in foreground (useful for debugging).
        Returns the PID if started, None if already running.
        """
        ensure_dirs()
        existing = read_pid()
        if existing and _is_process_running(existing):
            print(f"Shred-CLI is already running (PID {existing}).")
            sys.exit(1)

        if not daemonize:
            self._run_in_foreground()
            return None

        if platform.system() == "Windows":
            return self._start_windows_detached()
        else:
            return self._run_daemon_unix()

    def _start_windows_detached(self) -> int:
        import subprocess
        # Re-run this script in detached mode
        cmd = [sys.executable, "-m", "shredcli.cli", "start", "--no-daemon"]
        subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        # Wait briefly to allow PID to be written
        time.sleep(0.5)
        pid = read_pid()
        return pid or 0


def stop_daemon() -> bool:
    """
    Stop the daemon by reading PID and sending SIGTERM (Unix) or terminate (Windows).
    Returns True if stopped, False if not running.
    """
    import json

    pid = read_pid()
    if not pid:
        return False
    if not _is_process_running(pid):
        remove_pid()
        try:
            STATUS_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return False
    _terminate_process(pid)
    remove_pid()
    # Clear status file but keep it with stopped state
    try:
        STATUS_FILE.write_text(json.dumps({"running": False}))
    except Exception:
        pass
    return True


def get_status() -> dict:
    """
    Return a dict describing the daemon status.
    """
    pid = read_pid()
    running = bool(pid and _is_process_running(pid))
    return {
        "running": running,
        "pid": pid if running else None,
    }


def _is_process_running(pid: int) -> bool:
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Cannot signal, but process exists
            return True
        except Exception:
            return False


def _terminate_process(pid: int) -> None:
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
        except Exception:
            pass
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception:
            pass
