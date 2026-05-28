"""
Typing analytics and statistics tracking for Shred-CLI.
Tracks performance metrics, generates heatmaps, and maintains session history.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque, defaultdict
import threading


@dataclass
class KeystrokeEvent:
    """A single keystroke event."""
    timestamp: float
    key: str = ""  # Optional key identifier
    wpm_at_time: float = 0.0


@dataclass
class SessionStats:
    """Statistics for a single typing session."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_keystrokes: int = 0
    max_wpm: float = 0.0
    avg_wpm: float = 0.0
    total_time_typing: float = 0.0  # Time actively typing (not idle)
    chord_progressions_completed: int = 0
    
    # Time spent in each tempo zone
    time_in_adagio: float = 0.0      # 40-80 BPM
    time_in_andante: float = 0.0     # 80-120 BPM
    time_in_allegro: float = 0.0    # 120-160 BPM
    time_in_presto: float = 0.0     # 160+ BPM
    
    # Pattern distribution
    patterns_used: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def duration(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["duration_seconds"] = self.duration()
        return data


@dataclass
class TypingHeatmap:
    """Time-based typing heatmap data."""
    # WPM by minute of hour (0-59)
    wpm_by_minute: List[float] = field(default_factory=lambda: [0.0] * 60)
    # Keystroke count by hour (0-23)
    keystrokes_by_hour: List[int] = field(default_factory=lambda: [0] * 24)
    # WPM history over time
    wpm_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_sample(self, wpm: float, keystrokes: int = 1) -> None:
        """Add a WPM sample to the heatmap."""
        now = datetime.now()
        minute = now.minute
        hour = now.hour
        
        # Update running average for this minute
        current = self.wpm_by_minute[minute]
        self.wpm_by_minute[minute] = (current + wpm) / 2 if current > 0 else wpm
        
        # Add keystrokes to hour bucket
        self.keystrokes_by_hour[hour] += keystrokes
        
        # Add to history with timestamp
        self.wpm_history.append({
            "timestamp": time.time(),
            "wpm": wpm,
            "hour": hour,
            "minute": minute,
        })
    
    def get_peak_hour(self) -> tuple:
        """Get the hour with most keystrokes."""
        if not any(self.keystrokes_by_hour):
            return (0, 0)
        max_idx = max(range(24), key=lambda i: self.keystrokes_by_hour[i])
        return (max_idx, self.keystrokes_by_hour[max_idx])
    
    def get_average_wpm(self) -> float:
        """Calculate average WPM from history."""
        if not self.wpm_history:
            return 0.0
        return sum(s["wpm"] for s in self.wpm_history) / len(self.wpm_history)


@dataclass
class Achievement:
    """An unlockable achievement."""
    id: str
    name: str
    description: str
    icon: str
    condition_fn: Any = field(repr=False)  # Function to check if unlocked
    unlocked_at: Optional[float] = None
    
    def is_unlocked(self, stats: SessionStats, total_stats: 'UserStats') -> bool:
        """Check if achievement condition is met."""
        if self.unlocked_at is not None:
            return True
        return self.condition_fn(stats, total_stats)
    
    def unlock(self) -> None:
        """Mark achievement as unlocked."""
        if self.unlocked_at is None:
            self.unlocked_at = time.time()


@dataclass
class UserStats:
    """Persistent user statistics across all sessions."""
    total_sessions: int = 0
    total_keystrokes_all_time: int = 0
    total_typing_time: float = 0.0  # seconds
    highest_wpm_ever: float = 0.0
    longest_session: float = 0.0   # seconds
    total_chords_played: int = 0
    
    # Level progression
    current_level: int = 1
    current_xp: int = 0
    
    # Achievement tracking
    achievements_unlocked: List[str] = field(default_factory=list)
    
    # Session history (last 100 sessions)
    session_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add_session(self, session: SessionStats) -> int:
        """Add a completed session and calculate XP earned."""
        self.total_sessions += 1
        self.total_keystrokes_all_time += session.total_keystrokes
        self.total_typing_time += session.total_time_typing
        self.total_chords_played += session.chord_progressions_completed
        
        # Update records
        if session.max_wpm > self.highest_wpm_ever:
            self.highest_wpm_ever = session.max_wpm
        if session.duration() > self.longest_session:
            self.longest_session = session.duration()
        
        # Store session summary
        self.session_history.append({
            "date": datetime.now().isoformat(),
            "duration": session.duration(),
            "keystrokes": session.total_keystrokes,
            "max_wpm": session.max_wpm,
            "avg_wpm": session.avg_wpm,
        })
        
        # Calculate XP
        xp_earned = self._calculate_xp(session)
        self.current_xp += xp_earned
        
        # Check for level up
        return self._check_level_up()
    
    def _calculate_xp(self, session: SessionStats) -> int:
        """Calculate XP earned from a session."""
        xp = 0
        
        # Base XP from keystrokes
        xp += session.total_keystrokes // 10
        
        # Bonus for high WPM
        if session.max_wpm >= 100:
            xp += 100
        elif session.max_wpm >= 80:
            xp += 50
        elif session.max_wpm >= 60:
            xp += 25
        
        # Bonus for session length
        if session.duration() >= 300:  # 5 minutes
            xp += 50
        
        # Bonus for tempo zones
        xp += int(session.time_in_presto / 10)  # 1 XP per 10 seconds at presto
        xp += int(session.time_in_allegro / 20)
        
        return xp
    
    def _check_level_up(self) -> int:
        """Check if user should level up. Returns levels gained."""
        levels_gained = 0
        xp_needed = self.current_level * 1000
        
        while self.current_xp >= xp_needed:
            self.current_xp -= xp_needed
            self.current_level += 1
            levels_gained += 1
            xp_needed = self.current_level * 1000
        
        return levels_gained
    
    def xp_to_next_level(self) -> int:
        """Get XP needed for next level."""
        return self.current_level * 1000 - self.current_xp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_sessions": self.total_sessions,
            "total_keystrokes_all_time": self.total_keystrokes_all_time,
            "total_typing_time_hours": self.total_typing_time / 3600,
            "highest_wpm_ever": self.highest_wpm_ever,
            "longest_session_minutes": self.longest_session / 60,
            "total_chords_played": self.total_chords_played,
            "current_level": self.current_level,
            "current_xp": self.current_xp,
            "xp_to_next_level": self.xp_to_next_level(),
            "achievements_unlocked": self.achievements_unlocked,
            "recent_sessions": list(self.session_history)[-10:],
        }


class AnalyticsTracker:
    """
    Main analytics tracking class.
    Manages session stats, heatmap data, and achievements.
    """
    
    DATA_DIR = Path.home() / ".shredcli"
    STATS_FILE = DATA_DIR / "stats.json"
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current_session: Optional[SessionStats] = None
        self._heatmap = TypingHeatmap()
        self._user_stats = self._load_user_stats()
        self._achievements: List[Achievement] = []
        self._last_update = time.time()
        self._last_tempo_check = time.time()
        self._current_tempo_zone = "adagio"
        
        self._setup_achievements()
    
    def _setup_achievements(self) -> None:
        """Define all unlockable achievements."""
        self._achievements = [
            Achievement(
                id="first_key",
                name="First Steps",
                description="Type your first keystroke",
                icon="👶",
                condition_fn=lambda s, u: s.total_keystrokes >= 1,
            ),
            Achievement(
                id="speed_demon",
                name="Speed Demon",
                description="Reach 100 WPM",
                icon="⚡",
                condition_fn=lambda s, u: s.max_wpm >= 100,
            ),
            Achievement(
                id="marathon",
                name="Marathon Typist",
                description="Type for 5 minutes straight",
                icon="🏃",
                condition_fn=lambda s, u: s.total_time_typing >= 300,
            ),
            Achievement(
                id="century",
                name="Century Club",
                description="Type 100 keystrokes",
                icon="💯",
                condition_fn=lambda s, u: s.total_keystrokes >= 100,
            ),
            Achievement(
                id="shredder",
                name="Shredder",
                description="Spend 30 seconds at Presto tempo (160+ BPM)",
                icon="🔥",
                condition_fn=lambda s, u: s.time_in_presto >= 30,
            ),
            Achievement(
                id="maestro",
                name="Maestro",
                description="Complete 10 chord progressions",
                icon="🎼",
                condition_fn=lambda s, u: s.chord_progressions_completed >= 10,
            ),
            Achievement(
                id="all_patterns",
                name="Well Rounded",
                description="Use all 5 arpeggio patterns",
                icon="🎸",
                condition_fn=lambda s, u: len(s.patterns_used) >= 5,
            ),
            Achievement(
                id="lightning",
                name="Lightning Fingers",
                description="Reach 150 WPM",
                icon="🌩️",
                condition_fn=lambda s, u: s.max_wpm >= 150,
            ),
            Achievement(
                id="veteran",
                name="Veteran",
                description="Complete 10 sessions",
                icon="🎖️",
                condition_fn=lambda s, u: u.total_sessions >= 10,
            ),
            Achievement(
                id="master",
                name="Master Shredder",
                description="Reach level 10",
                icon="👑",
                condition_fn=lambda s, u: u.current_level >= 10,
            ),
        ]
    
    def _load_user_stats(self) -> UserStats:
        """Load user stats from disk."""
        try:
            if self.STATS_FILE.exists():
                with open(self.STATS_FILE, "r") as f:
                    data = json.load(f)
                    stats = UserStats()
                    stats.total_sessions = data.get("total_sessions", 0)
                    stats.total_keystrokes_all_time = data.get("total_keystrokes_all_time", 0)
                    stats.total_typing_time = data.get("total_typing_time", 0)
                    stats.highest_wpm_ever = data.get("highest_wpm_ever", 0)
                    stats.longest_session = data.get("longest_session", 0)
                    stats.total_chords_played = data.get("total_chords_played", 0)
                    stats.current_level = data.get("current_level", 1)
                    stats.current_xp = data.get("current_xp", 0)
                    stats.achievements_unlocked = data.get("achievements_unlocked", [])
                    history = data.get("session_history", [])
                    stats.session_history = deque(history, maxlen=100)
                    return stats
        except Exception:
            pass
        return UserStats()
    
    def save(self) -> None:
        """Save user stats to disk."""
        try:
            self.DATA_DIR.mkdir(parents=True, exist_ok=True)
            stats = self._user_stats
            payload = {
                "total_sessions": stats.total_sessions,
                "total_keystrokes_all_time": stats.total_keystrokes_all_time,
                "total_typing_time": stats.total_typing_time,
                "highest_wpm_ever": stats.highest_wpm_ever,
                "longest_session": stats.longest_session,
                "total_chords_played": stats.total_chords_played,
                "current_level": stats.current_level,
                "current_xp": stats.current_xp,
                "achievements_unlocked": stats.achievements_unlocked,
                "session_history": list(stats.session_history),
            }
            with open(self.STATS_FILE, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass
    
    def start_session(self) -> None:
        """Start tracking a new session."""
        with self._lock:
            self._current_session = SessionStats()
            self._last_update = time.time()
            self._last_tempo_check = time.time()
            self._current_tempo_zone = "adagio"
    
    def end_session(self) -> tuple:
        """End current session and return stats + any new achievements."""
        with self._lock:
            if self._current_session:
                self._current_session.end_time = time.time()
                
                # Update tempo zone time
                self._update_tempo_time()
                
                # Add to user stats
                levels_gained = self._user_stats.add_session(self._current_session)
                
                # Check achievements
                new_achievements = self._check_achievements()
                
                # Save to disk
                self.save()
                
                result = (self._current_session, new_achievements, levels_gained)
                self._current_session = None
                return result
            return (None, [], 0)
    
    def record_keystroke(self, wpm: float = 0.0) -> None:
        """Record a keystroke in current session."""
        with self._lock:
            if self._current_session:
                now = time.time()
                self._current_session.total_keystrokes += 1
                
                # Update WPM tracking
                if wpm > self._current_session.max_wpm:
                    self._current_session.max_wpm = wpm
                
                # Update heatmap
                self._heatmap.add_sample(wpm, 1)
                
                # Check idle time
                if now - self._last_update < 3.0:  # Not idle
                    self._current_session.total_time_typing += now - self._last_update
                
                self._last_update = now
    
    def record_bpm(self, bpm: float, pattern: str) -> None:
        """Record current BPM for tempo tracking."""
        with self._lock:
            self._update_tempo_time()
            
            # Determine new tempo zone
            if bpm >= 160:
                self._current_tempo_zone = "presto"
            elif bpm >= 120:
                self._current_tempo_zone = "allegro"
            elif bpm >= 80:
                self._current_tempo_zone = "andante"
            else:
                self._current_tempo_zone = "adagio"
            
            self._last_tempo_check = time.time()
            
            # Track pattern usage
            if self._current_session:
                self._current_session.patterns_used[pattern] += 1
    
    def _update_tempo_time(self) -> None:
        """Update time spent in current tempo zone."""
        if not self._current_session:
            return
        
        elapsed = time.time() - self._last_tempo_check
        
        if self._current_tempo_zone == "presto":
            self._current_session.time_in_presto += elapsed
        elif self._current_tempo_zone == "allegro":
            self._current_session.time_in_allegro += elapsed
        elif self._current_tempo_zone == "andante":
            self._current_session.time_in_andante += elapsed
        else:
            self._current_session.time_in_adagio += elapsed
    
    def record_chord_progression(self) -> None:
        """Record completion of a chord progression cycle."""
        with self._lock:
            if self._current_session:
                self._current_session.chord_progressions_completed += 1
    
    def _check_achievements(self) -> List[Achievement]:
        """Check and unlock any new achievements."""
        new_achievements = []
        
        for achievement in self._achievements:
            if achievement.id not in self._user_stats.achievements_unlocked:
                if achievement.is_unlocked(self._current_session, self._user_stats):
                    achievement.unlock()
                    self._user_stats.achievements_unlocked.append(achievement.id)
                    new_achievements.append(achievement)
        
        return new_achievements
    
    def get_current_stats(self) -> Optional[SessionStats]:
        """Get current session stats."""
        with self._lock:
            if self._current_session:
                # Update tempo time before returning
                self._update_tempo_time()
                self._last_tempo_check = time.time()
            return self._current_session
    
    def get_user_summary(self) -> Dict[str, Any]:
        """Get summary of all user stats."""
        with self._lock:
            return {
                "user": self._user_stats.to_dict(),
                "heatmap": {
                    "peak_hour": self._heatmap.get_peak_hour(),
                    "avg_wpm": self._heatmap.get_average_wpm(),
                },
                "achievements": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "description": a.description,
                        "icon": a.icon,
                        "unlocked": a.id in self._user_stats.achievements_unlocked,
                    }
                    for a in self._achievements
                ],
            }
    
    def get_current_level_info(self) -> Dict[str, Any]:
        """Get current level and XP info."""
        with self._lock:
            return {
                "level": self._user_stats.current_level,
                "xp": self._user_stats.current_xp,
                "xp_needed": self._user_stats.xp_to_next_level(),
                "progress_pct": (
                    self._user_stats.current_xp / 
                    (self._user_stats.current_level * 1000) * 100
                ),
            }


# Global analytics instance
_analytics: Optional[AnalyticsTracker] = None


def get_analytics() -> AnalyticsTracker:
    """Get or create global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsTracker()
    return _analytics
