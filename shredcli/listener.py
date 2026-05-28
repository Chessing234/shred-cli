"""
Global keyboard listener + WPM calculator using sliding window.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Optional


def _keyboard_listener(**kwargs: Any) -> Any:
    """Lazy import so headless CI can collect tests without an X display."""
    from pynput import keyboard

    return keyboard.Listener(**kwargs)


class WpmCalculator:
    """
    Maintain sliding window of last 10 keystrokes.
    WPM = (keystrokes / 5) / (elapsed_seconds / 60)
    """

    def __init__(self, window_size: int = 10) -> None:
        self._window_size = window_size
        self._timestamps: deque[float] = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._last_key_time: float = 0.0

    def add_keystroke(self) -> None:
        """Record a keystroke timestamp."""
        now = time.time()
        with self._lock:
            self._timestamps.append(now)
            self._last_key_time = now

    def get_wpm(self) -> float:
        """Calculate current WPM based on windowed keystrokes."""
        with self._lock:
            if len(self._timestamps) < 2:
                return 0.0
            elapsed = self._timestamps[-1] - self._timestamps[0]
            if elapsed <= 0.0:
                return 0.0
            kps = len(self._timestamps) / elapsed
            wpm = (kps * 60) / 5
            return wpm

    def seconds_since_last_key(self) -> float:
        """Idle time since last keystroke."""
        with self._lock:
            return time.time() - self._last_key_time

    def reset(self) -> None:
        """Clear the sliding window."""
        with self._lock:
            self._timestamps.clear()
            self._last_key_time = 0.0


class KeyListener:
    """
    Non-blocking global key listener using pynput.
    Only records keystrokes, never intercepts or consumes them.
    """

    def __init__(
        self,
        on_keystroke: Callable[[], None],
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_keystroke = on_keystroke
        self._on_start = on_start
        self._on_stop = on_stop
        self._listener: Optional[Any] = None
        self._running = False
        self._lock = threading.Lock()

    def _on_press(self, key) -> None:
        """Record any press as a keystroke; do not swallow."""
        try:
            self._on_keystroke()
        except Exception:
            pass

    def start(self) -> None:
        """Start listening in a background thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._listener = _keyboard_listener(
                on_press=self._on_press,
                on_release=None,
                suppress=False,
            )
            self._listener.start()
        if self._on_start:
            self._on_start()

    def stop(self) -> None:
        """Stop the listener."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._listener:
                self._listener.stop()
                self._listener = None
        if self._on_stop:
            self._on_stop()

    def is_running(self) -> bool:
        with self._lock:
            return self._running


class WpmSmoother:
    """
    Exponential smoothing for BPM transitions.
    new_BPM = 0.8 * current_BPM + 0.2 * target_BPM
    Update every 500ms.
    """

    def __init__(self, initial_bpm: float = 40.0) -> None:
        self._current = initial_bpm
        self._lock = threading.Lock()

    def update(self, target_bpm: float) -> float:
        """Apply smoothing and return the new BPM."""
        with self._lock:
            self._current = 0.8 * self._current + 0.2 * target_bpm
            return self._current

    def get(self) -> float:
        with self._lock:
            return self._current

    def set(self, value: float) -> None:
        with self._lock:
            self._current = value


class AutoSlowdown:
    """
    If no keystrokes for 3 seconds, gracefully slow BPM back to 40 over 2 seconds.
    """

    def __init__(
        self,
        wpm_calc: WpmCalculator,
        smoother: WpmSmoother,
        idle_threshold: float = 3.0,
        slowdown_duration: float = 2.0,
        min_bpm: float = 40.0,
    ) -> None:
        self._calc = wpm_calc
        self._smoother = smoother
        self._idle_threshold = idle_threshold
        self._slowdown_duration = slowdown_duration
        self._min_bpm = min_bpm
        self._slowdown_start: Optional[float] = None
        self._slowdown_from: float = min_bpm

    def tick(self, current_bpm: float) -> float:
        """
        Called periodically; returns adjusted BPM based on idle state.
        """
        idle = self._calc.seconds_since_last_key()
        if idle >= self._idle_threshold:
            # Start or continue slowdown
            if self._slowdown_start is None:
                self._slowdown_start = time.time()
                self._slowdown_from = current_bpm
            elapsed = time.time() - self._slowdown_start
            if elapsed >= self._slowdown_duration:
                # Reached min, hold there until next keypress
                self._smoother.set(self._min_bpm)
                return self._min_bpm
            # Linear descent to min over 2s
            ratio = elapsed / self._slowdown_duration
            target = self._slowdown_from + (self._min_bpm - self._slowdown_from) * ratio
            return self._smoother.update(target)
        else:
            # Active typing
            self._slowdown_start = None
            return current_bpm
