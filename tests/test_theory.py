"""
Tests for theory module: chords and arpeggio patterns.
"""

import pytest

from shredcli.theory import (
    PROGRESSION,
    PATTERN_FUNCTIONS,
    PATTERN_LABELS,
    pattern_a,
    pattern_b,
    pattern_c,
    pattern_d,
    pattern_e,
    expand_pattern_to_sixteenths,
    CH_BASS,
    CH_MID,
    CH_TREBLE,
)


class TestVoicings:
    """Test chord voicings."""

    def test_progression_has_6_chords(self):
        assert len(PROGRESSION) == 6

    def test_am_voicing(self):
        am = PROGRESSION[0]
        assert am.name == "Am"
        # Am: [A2(45), E3(52), A3(57), C4(60), E4(64), A4(69)]
        assert am.bass == (45, 52)
        assert am.mid == (57, 60)
        assert am.treble == (64, 69)

    def test_dm_voicing(self):
        dm = PROGRESSION[1]
        assert dm.name == "Dm"

    def test_e7_voicing(self):
        e7 = PROGRESSION[2]
        assert e7.name == "E7"

    def test_f_voicing(self):
        f = PROGRESSION[3]
        assert f.name == "F"

    def test_c_voicing(self):
        c = PROGRESSION[4]
        assert c.name == "C"

    def test_g_voicing(self):
        g = PROGRESSION[5]
        assert g.name == "G"

    def test_all_notes_returns_list(self):
        am = PROGRESSION[0]
        notes = am.all_notes()
        assert isinstance(notes, list)
        assert len(notes) == 6


class TestPatterns:
    """Test arpeggio patterns."""

    def test_pattern_a_returns_steps(self):
        am = PROGRESSION[0]
        steps = pattern_a(am)
        assert len(steps) == 4

    def test_pattern_b_returns_steps(self):
        am = PROGRESSION[0]
        steps = pattern_b(am)
        assert len(steps) == 4

    def test_pattern_c_returns_steps(self):
        am = PROGRESSION[0]
        steps = pattern_c(am)
        assert len(steps) == 5

    def test_pattern_d_returns_steps(self):
        am = PROGRESSION[0]
        steps = pattern_d(am)
        assert len(steps) == 5

    def test_pattern_e_returns_steps(self):
        am = PROGRESSION[0]
        steps = pattern_e(am)
        # Up 6 notes then down 6 notes
        assert len(steps) == 12

    def test_pattern_channels_valid(self):
        """Ensure all notes map to valid channels."""
        am = PROGRESSION[0]
        for pattern_fn in PATTERN_FUNCTIONS:
            steps = pattern_fn(am)
            for step in steps:
                for ch, note in step:
                    assert ch in (CH_BASS, CH_MID, CH_TREBLE)
                    assert 0 <= note <= 127


class TestExpandPattern:
    """Test pattern expansion to 32 sixteenths."""

    def test_expands_to_32_steps(self):
        am = PROGRESSION[0]
        steps = pattern_a(am)
        expanded = expand_pattern_to_sixteenths(steps, 32)
        assert len(expanded) == 32

    def test_expands_short_pattern(self):
        am = PROGRESSION[0]
        steps = pattern_a(am)  # 4 steps
        expanded = expand_pattern_to_sixteenths(steps, 32)
        assert len(expanded) == 32
        # Should repeat the pattern 8 times


class TestPatternLabels:
    """Test pattern label constants."""

    def test_5_pattern_labels(self):
        assert len(PATTERN_LABELS) == 5
        assert PATTERN_LABELS == ("A", "B", "C", "D", "E")

    def test_5_pattern_functions(self):
        assert len(PATTERN_FUNCTIONS) == 5
