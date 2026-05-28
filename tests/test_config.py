"""
Tests for config module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from shredcli.config import (
    ShredConfig,
    DEFAULT_CONFIG,
    load_config_file,
    save_config_file,
    map_wpm_to_bpm,
    _deep_merge,
)


class TestShredConfig:
    """Test configuration dataclass."""

    def test_default_config(self):
        cfg = ShredConfig.from_defaults()
        assert cfg.midi_port == "ShredCLI"
        assert cfg.min_bpm == 40.0
        assert cfg.max_bpm == 200.0
        assert cfg.smoothing_alpha == 0.2
        assert cfg.update_interval_ms == 500
        assert cfg.idle_threshold_seconds == 3.0
        assert cfg.window_size == 10

    def test_config_from_dict(self):
        data = {
            "midi_port": "CustomPort",
            "min_bpm": 60.0,
            "max_bpm": 180.0,
        }
        cfg = ShredConfig.from_dict(data)
        assert cfg.midi_port == "CustomPort"
        assert cfg.min_bpm == 60.0
        assert cfg.max_bpm == 180.0
        # Other values use defaults
        assert cfg.window_size == 10

    def test_config_to_dict(self):
        cfg = ShredConfig.from_defaults()
        data = cfg.to_dict()
        assert data["midi_port"] == "ShredCLI"
        assert data["min_bpm"] == 40.0


class TestWpmToBpmMapping:
    """Test WPM to BPM mapping function."""

    def test_zero_wpm_returns_min_bpm(self):
        bpm = map_wpm_to_bpm(0)
        assert bpm == 40.0

    def test_negative_wpm_returns_min_bpm(self):
        bpm = map_wpm_to_bpm(-5)
        assert bpm == 40.0

    def test_10_wpm_in_adagio_range(self):
        bpm = map_wpm_to_bpm(10)
        assert 40 <= bpm <= 80

    def test_20_wpm_at_boundary(self):
        bpm = map_wpm_to_bpm(20)
        assert bpm == 80.0

    def test_40_wpm_in_andante_range(self):
        bpm = map_wpm_to_bpm(40)
        assert 80 <= bpm <= 120

    def test_60_wpm_at_boundary(self):
        bpm = map_wpm_to_bpm(60)
        assert bpm == 120.0

    def test_80_wpm_in_allegro_range(self):
        bpm = map_wpm_to_bpm(80)
        assert 120 <= bpm <= 160

    def test_100_wpm_at_boundary(self):
        bpm = map_wpm_to_bpm(100)
        assert bpm == 160.0

    def test_120_wpm_in_presto_range(self):
        bpm = map_wpm_to_bpm(120)
        assert 160 <= bpm <= 200

    def test_200_wpm_capped_at_max(self):
        bpm = map_wpm_to_bpm(200)
        assert bpm == 200.0

    def test_linear_interpolation_within_ranges(self):
        # Test that values increase monotonically
        bpms = [map_wpm_to_bpm(wpm) for wpm in range(0, 151, 10)]
        for i in range(1, len(bpms)):
            assert bpms[i] >= bpms[i - 1]


class TestConfigFile:
    """Test configuration file loading and saving."""

    def test_load_nonexistent_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"
            config = load_config_file(path)
            assert config == DEFAULT_CONFIG

    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            test_config = {
                "midi": {"port_name": "TestPort"},
                "timing": {"min_bpm": 50.0},
            }
            save_config_file(test_config, path)
            loaded = load_config_file(path)

            assert loaded["midi"]["port_name"] == "TestPort"
            assert loaded["timing"]["min_bpm"] == 50.0

    def test_load_invalid_json_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text("not valid json")
            config = load_config_file(path)
            assert config == DEFAULT_CONFIG


class TestDeepMerge:
    """Test deep merge functionality."""

    def test_simple_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        _deep_merge(base, override)
        assert base == {"a": 1, "b": 3}

    def test_nested_merge(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 5}}
        _deep_merge(base, override)
        assert base == {"a": {"x": 1, "y": 5}, "b": 3}

    def test_add_new_nested_key(self):
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}, "b": 3}
        _deep_merge(base, override)
        assert base == {"a": {"x": 1, "y": 2}, "b": 3}

    def test_override_with_dict(self):
        base = {"a": {"x": 1}}
        override = {"a": 2}
        _deep_merge(base, override)
        assert base == {"a": 2}
