"""
Configuration management for Shred-CLI.
Provides default settings and user-configurable overrides.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    # WPM to BPM mapping
    "wpm_to_bpm": {
        "ranges": [
            {"wpm_min": 0, "wpm_max": 20, "bpm_min": 40, "bpm_max": 80},
            {"wpm_min": 20, "wpm_max": 60, "bpm_min": 80, "bpm_max": 120},
            {"wpm_min": 60, "wpm_max": 100, "bpm_min": 120, "bpm_max": 160},
            {"wpm_min": 100, "wpm_max": 9999, "bpm_min": 160, "bpm_max": 200},
        ]
    },
    # Timing settings
    "timing": {
        "smoothing_alpha": 0.2,  # Exponential smoothing factor (0-1)
        "update_interval_ms": 500,  # How often to update BPM
        "idle_threshold_seconds": 3.0,
        "slowdown_duration_seconds": 2.0,
        "min_bpm": 40.0,
        "max_bpm": 200.0,
    },
    # Key listener
    "listener": {
        "window_size": 10,  # Sliding window for WPM calculation
    },
    # MIDI settings
    "midi": {
        "port_name": "ShredCLI",
        "tick_ms": 10,  # Scheduler resolution
        "note_duration_factor": 0.9,  # Note duration as fraction of subdivision
    },
    # Velocity ranges per voice
    "velocity": {
        "bass": {"min": 90, "max": 110},
        "mid": {"min": 60, "max": 80},
        "treble": {"min": 70, "max": 95},
        "jitter": 10,  # Random ±jitter
    },
    # Arpeggio settings
    "arpeggio": {
        "chord_duration_beats": 8,
        "subdivisions_per_beat": 4,  # 16th notes
    },
}


@dataclass
class ShredConfig:
    """Runtime configuration for Shred-CLI."""

    midi_port: str = "ShredCLI"
    min_bpm: float = 40.0
    max_bpm: float = 200.0
    smoothing_alpha: float = 0.2
    update_interval_ms: int = 500
    idle_threshold_seconds: float = 3.0
    slowdown_duration_seconds: float = 2.0
    window_size: int = 10
    tick_ms: int = 10
    note_duration_factor: float = 0.9
    velocity_jitter: int = 10

    @classmethod
    def from_defaults(cls) -> ShredConfig:
        """Create configuration from defaults."""
        return cls(
            midi_port=DEFAULT_CONFIG["midi"]["port_name"],
            min_bpm=DEFAULT_CONFIG["timing"]["min_bpm"],
            max_bpm=DEFAULT_CONFIG["timing"]["max_bpm"],
            smoothing_alpha=DEFAULT_CONFIG["timing"]["smoothing_alpha"],
            update_interval_ms=DEFAULT_CONFIG["timing"]["update_interval_ms"],
            idle_threshold_seconds=DEFAULT_CONFIG["timing"]["idle_threshold_seconds"],
            slowdown_duration_seconds=DEFAULT_CONFIG["timing"]["slowdown_duration_seconds"],
            window_size=DEFAULT_CONFIG["listener"]["window_size"],
            tick_ms=DEFAULT_CONFIG["midi"]["tick_ms"],
            note_duration_factor=DEFAULT_CONFIG["midi"]["note_duration_factor"],
            velocity_jitter=DEFAULT_CONFIG["velocity"]["jitter"],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShredConfig:
        """Create configuration from dictionary."""
        return cls(
            midi_port=data.get("midi_port", DEFAULT_CONFIG["midi"]["port_name"]),
            min_bpm=data.get("min_bpm", DEFAULT_CONFIG["timing"]["min_bpm"]),
            max_bpm=data.get("max_bpm", DEFAULT_CONFIG["timing"]["max_bpm"]),
            smoothing_alpha=data.get("smoothing_alpha", DEFAULT_CONFIG["timing"]["smoothing_alpha"]),
            update_interval_ms=data.get("update_interval_ms", DEFAULT_CONFIG["timing"]["update_interval_ms"]),
            idle_threshold_seconds=data.get("idle_threshold_seconds", DEFAULT_CONFIG["timing"]["idle_threshold_seconds"]),
            slowdown_duration_seconds=data.get("slowdown_duration_seconds", DEFAULT_CONFIG["timing"]["slowdown_duration_seconds"]),
            window_size=data.get("window_size", DEFAULT_CONFIG["listener"]["window_size"]),
            tick_ms=data.get("tick_ms", DEFAULT_CONFIG["midi"]["tick_ms"]),
            note_duration_factor=data.get("note_duration_factor", DEFAULT_CONFIG["midi"]["note_duration_factor"]),
            velocity_jitter=data.get("velocity_jitter", DEFAULT_CONFIG["velocity"]["jitter"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)


def load_config_file(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    If path is None, use ~/.shredcli/config.json
    """
    if path is None:
        path = Path.home() / ".shredcli" / "config.json"

    if not path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(path, "r") as f:
            user_config = json.load(f)
        # Merge with defaults
        config = DEFAULT_CONFIG.copy()
        _deep_merge(config, user_config)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file: {e}")
        return DEFAULT_CONFIG.copy()


def save_config_file(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Save configuration to JSON file.
    If path is None, use ~/.shredcli/config.json
    """
    if path is None:
        path = Path.home() / ".shredcli" / "config.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """Deep merge override dict into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def map_wpm_to_bpm(wpm: float, config: Optional[ShredConfig] = None) -> float:
    """
    Map WPM to BPM using the configured ranges.
    """
    cfg = config or ShredConfig.from_defaults()

    if wpm <= 0:
        return cfg.min_bpm
    if wpm <= 20:
        t = wpm / 20.0
        return 40.0 + t * (80.0 - 40.0)
    if wpm <= 60:
        t = (wpm - 20.0) / 40.0
        return 80.0 + t * (120.0 - 80.0)
    if wpm <= 100:
        t = (wpm - 60.0) / 40.0
        return 120.0 + t * (160.0 - 120.0)
    t = min((wpm - 100.0) / 50.0, 1.0)
    return 160.0 + t * (cfg.max_bpm - 160.0)
