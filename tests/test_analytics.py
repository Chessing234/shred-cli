"""Tests for analytics persistence and achievements."""

import json
import tempfile
from pathlib import Path

from shredcli.analytics import AnalyticsTracker, SessionStats, UserStats


class TestUserStats:
    def test_xp_and_level_up(self):
        user = UserStats()
        session = SessionStats(total_keystrokes=500, max_wpm=110)
        session.end_time = session.start_time + 400
        levels = user.add_session(session)
        assert user.current_xp > 0
        assert user.total_sessions == 1


class TestAnalyticsPersistence:
    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            stats_file = data_dir / "stats.json"

            tracker = AnalyticsTracker()
            tracker.STATS_FILE = stats_file
            tracker.DATA_DIR = data_dir
            tracker._user_stats.current_level = 3
            tracker._user_stats.current_xp = 250
            tracker._user_stats.total_keystrokes_all_time = 999
            tracker._user_stats.achievements_unlocked = ["first_key"]
            tracker.save()

            tracker2 = AnalyticsTracker()
            tracker2.STATS_FILE = stats_file
            tracker2.DATA_DIR = data_dir
            loaded = tracker2._load_user_stats()
            assert loaded.current_level == 3
            assert loaded.current_xp == 250
            assert loaded.total_keystrokes_all_time == 999
            assert "first_key" in loaded.achievements_unlocked

    def test_achievement_unlock_first_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            stats_file = data_dir / "stats.json"
            tracker = AnalyticsTracker()
            tracker.STATS_FILE = stats_file
            tracker.DATA_DIR = data_dir
            tracker._user_stats = UserStats()
            tracker._setup_achievements()
            tracker.start_session()
            tracker.record_keystroke(0)
            stats, achievements, _ = tracker.end_session()
            assert stats.total_keystrokes >= 1
            assert any(a.id == "first_key" for a in achievements)
