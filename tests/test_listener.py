"""
Tests for listener module: WPM calculator and keyboard listener.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from shredcli.listener import (
    WpmCalculator,
    WpmSmoother,
    AutoSlowdown,
    KeyListener,
)


class TestWpmCalculator:
    """Test WPM calculation."""

    def test_empty_window_returns_zero(self):
        calc = WpmCalculator(window_size=10)
        assert calc.get_wpm() == 0.0

    def test_single_keystroke_returns_zero(self):
        calc = WpmCalculator(window_size=10)
        calc.add_keystroke()
        assert calc.get_wpm() == 0.0

    def test_two_keystrokes_calculates_wpm(self):
        calc = WpmCalculator(window_size=10)
        calc.add_keystroke()
        time.sleep(0.01)  # 10ms
        calc.add_keystroke()
        wpm = calc.get_wpm()
        assert wpm > 0

    def test_window_size_limits_keystrokes(self):
        calc = WpmCalculator(window_size=3)
        for _ in range(5):
            calc.add_keystroke()
            time.sleep(0.01)
        # Only 3 keystrokes should be in window
        # WPM calculation uses window size

    def test_reset_clears_window(self):
        calc = WpmCalculator(window_size=10)
        calc.add_keystroke()
        time.sleep(0.01)
        calc.add_keystroke()
        calc.reset()
        assert calc.get_wpm() == 0.0

    def test_seconds_since_last_key_increases(self):
        calc = WpmCalculator(window_size=10)
        calc.add_keystroke()
        time.sleep(0.05)
        idle = calc.seconds_since_last_key()
        assert idle >= 0.04  # Allow some tolerance


class TestWpmSmoother:
    """Test exponential smoothing."""

    def test_initial_bpm(self):
        smoother = WpmSmoother(initial_bpm=40.0)
        assert smoother.get() == 40.0

    def test_update_applies_smoothing(self):
        smoother = WpmSmoother(initial_bpm=40.0)
        # new = 0.8*40 + 0.2*100 = 32 + 20 = 52
        result = smoother.update(100.0)
        assert result == 52.0

    def test_multiple_updates_converge(self):
        smoother = WpmSmoother(initial_bpm=40.0)
        for _ in range(20):
            smoother.update(120.0)
        # Should converge close to 120
        assert smoother.get() > 100

    def test_set_overrides_value(self):
        smoother = WpmSmoother(initial_bpm=40.0)
        smoother.set(80.0)
        assert smoother.get() == 80.0


class TestAutoSlowdown:
    """Test auto-slowdown when idle."""

    def test_active_typing_no_slowdown(self):
        calc = WpmCalculator(window_size=10)
        smoother = WpmSmoother(initial_bpm=100.0)
        slowdown = AutoSlowdown(
            wpm_calc=calc,
            smoother=smoother,
            idle_threshold=0.5,
            slowdown_duration=1.0,
            min_bpm=40.0,
        )
        # Add keystroke to be active
        calc.add_keystroke()
        result = slowdown.tick(100.0)
        assert result == 100.0  # No slowdown when active

    def test_idle_triggers_slowdown(self):
        calc = WpmCalculator(window_size=10)
        smoother = WpmSmoother(initial_bpm=100.0)
        slowdown = AutoSlowdown(
            wpm_calc=calc,
            smoother=smoother,
            idle_threshold=0.01,  # Very short for testing
            slowdown_duration=0.1,
            min_bpm=40.0,
        )
        # Don't add keystrokes - wait for idle
        time.sleep(0.02)
        result = slowdown.tick(100.0)
        # Should be slowing down
        assert result < 100.0


class TestKeyListener:
    """Test keyboard listener."""

    def test_listener_creation(self):
        callback = MagicMock()
        listener = KeyListener(on_keystroke=callback)
        assert listener is not None

    @patch('shredcli.listener.keyboard.Listener')
    def test_start_creates_listener(self, mock_listener_class):
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener
        
        callback = MagicMock()
        listener = KeyListener(on_keystroke=callback)
        listener.start()
        
        mock_listener_class.assert_called_once()
        mock_listener.start.assert_called_once()

    @patch('shredcli.listener.keyboard.Listener')
    def test_stop_stops_listener(self, mock_listener_class):
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener
        
        callback = MagicMock()
        listener = KeyListener(on_keystroke=callback)
        listener.start()
        listener.stop()
        
        mock_listener.stop.assert_called_once()
