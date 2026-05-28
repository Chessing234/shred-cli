"""
Tests for daemon module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from shredcli.daemon import (
    DATA_DIR,
    PID_FILE,
    LOG_FILE,
    ensure_dirs,
    read_pid,
    write_pid,
    remove_pid,
    read_status,
    write_status,
    get_status,
    _is_process_running,
    _terminate_process,
    stop_daemon,
)


class TestDirectories:
    """Test directory creation."""

    def test_ensure_dirs_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / ".shredcli"
            with patch('shredcli.daemon.DATA_DIR', data_dir):
                ensure_dirs()
                assert data_dir.exists()


class TestPIDFile:
    """Test PID file operations."""

    def test_write_and_read_pid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "shred.pid"
            with patch('shredcli.daemon.PID_FILE', pid_file):
                write_pid(12345)
                assert read_pid() == 12345

    def test_read_nonexistent_pid_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "nonexistent.pid"
            with patch('shredcli.daemon.PID_FILE', pid_file):
                assert read_pid() is None

    def test_remove_pid_deletes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "shred.pid"
            with patch('shredcli.daemon.PID_FILE', pid_file):
                write_pid(12345)
                assert pid_file.exists()
                remove_pid()
                assert not pid_file.exists()

    def test_read_invalid_pid_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "shred.pid"
            pid_file.write_text("not a number")
            with patch('shredcli.daemon.PID_FILE', pid_file):
                assert read_pid() is None


class TestStatusFile:
    """Test status file operations."""

    def test_write_and_read_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            with patch('shredcli.daemon.STATUS_FILE', status_file):
                data = {"running": True, "bpm": 120.5}
                write_status(data)
                loaded = read_status()
                assert loaded["running"] is True
                assert loaded["bpm"] == 120.5

    def test_read_nonexistent_status_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "nonexistent.json"
            with patch('shredcli.daemon.STATUS_FILE', status_file):
                assert read_status() == {}

    def test_read_invalid_json_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_file.write_text("not json")
            with patch('shredcli.daemon.STATUS_FILE', status_file):
                assert read_status() == {}


class TestGetStatus:
    """Test get_status function."""

    @patch('shredcli.daemon.read_pid')
    @patch('shredcli.daemon._is_process_running')
    def test_not_running_no_pid(self, mock_running, mock_read_pid):
        mock_read_pid.return_value = None
        status = get_status()
        assert status["running"] is False
        assert status["pid"] is None

    @patch('shredcli.daemon.read_pid')
    @patch('shredcli.daemon._is_process_running')
    def test_not_running_dead_pid(self, mock_running, mock_read_pid):
        mock_read_pid.return_value = 99999
        mock_running.return_value = False
        status = get_status()
        assert status["running"] is False
        assert status["pid"] is None

    @patch('shredcli.daemon.read_pid')
    @patch('shredcli.daemon._is_process_running')
    def test_running_with_live_pid(self, mock_running, mock_read_pid):
        mock_read_pid.return_value = 12345
        mock_running.return_value = True
        status = get_status()
        assert status["running"] is True
        assert status["pid"] == 12345


class TestIsProcessRunning:
    """Test process detection."""

    def test_own_process_is_running(self):
        # Our own PID should be running
        assert _is_process_running(os.getpid()) is True

    def test_nonexistent_process_not_running(self):
        # High PID unlikely to exist
        assert _is_process_running(999999) is False


class TestStopDaemon:
    """Test stop_daemon function."""

    @patch('shredcli.daemon.read_pid')
    def test_stop_no_pid_returns_false(self, mock_read_pid):
        mock_read_pid.return_value = None
        assert stop_daemon() is False

    @patch('shredcli.daemon.read_pid')
    @patch('shredcli.daemon._is_process_running')
    def test_stop_dead_pid_returns_false(self, mock_running, mock_read_pid):
        mock_read_pid.return_value = 99999
        mock_running.return_value = False
        assert stop_daemon() is False

    @patch('shredcli.daemon.read_pid')
    @patch('shredcli.daemon._is_process_running')
    @patch('shredcli.daemon._terminate_process')
    def test_stop_live_pid_returns_true(self, mock_terminate, mock_running, mock_read_pid):
        mock_read_pid.return_value = 12345
        mock_running.return_value = True
        assert stop_daemon() is True
        mock_terminate.assert_called_once_with(12345)
