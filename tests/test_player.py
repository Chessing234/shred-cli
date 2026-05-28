"""
Tests for player module: MIDI scheduling and arpeggio engine.
"""

import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from shredcli.player import (
    MidiEvent,
    VelocityHumaniser,
    ArpeggioEngine,
    ALL_CHANNELS,
    CH_BASS,
    CH_MID,
    CH_TREBLE,
)
from shredcli.theory import PROGRESSION, CH_BASS, CH_MID, CH_TREBLE


class TestMidiEvent:
    """Test MIDI event dataclass."""

    def test_event_creation(self):
        ev = MidiEvent(
            time_ms=1000.0,
            kind_priority=1,
            channel=0,
            note=60,
            velocity=100,
        )
        assert ev.time_ms == 1000.0
        assert ev.kind_priority == 1
        assert ev.channel == 0
        assert ev.note == 60
        assert ev.velocity == 100

    def test_event_sorting(self):
        """Events should sort by time, then by kind_priority."""
        ev1 = MidiEvent(time_ms=1000.0, kind_priority=1, channel=0, note=60, velocity=100)
        ev2 = MidiEvent(time_ms=1000.0, kind_priority=0, channel=0, note=60, velocity=0)
        ev3 = MidiEvent(time_ms=2000.0, kind_priority=1, channel=0, note=62, velocity=100)

        events = [ev3, ev1, ev2]
        events.sort()

        # ev2 (note_off) comes before ev1 (note_on) at same time
        assert events[0] == ev2
        assert events[1] == ev1
        assert events[2] == ev3


class TestVelocityHumaniser:
    """Test velocity humanization."""

    def test_bass_velocity_range(self):
        h = VelocityHumaniser()
        for _ in range(20):
            vel = h.get_velocity(CH_BASS)
            assert 80 <= vel <= 120  # 90-110 with ±10 jitter
            assert 1 <= vel <= 127

    def test_mid_velocity_range(self):
        h = VelocityHumaniser()
        for _ in range(20):
            vel = h.get_velocity(CH_MID)
            assert 50 <= vel <= 90  # 60-80 with ±10 jitter
            assert 1 <= vel <= 127

    def test_treble_velocity_range(self):
        h = VelocityHumaniser()
        for _ in range(20):
            vel = h.get_velocity(CH_TREBLE)
            assert 60 <= vel <= 105  # 70-95 with ±10 jitter
            assert 1 <= vel <= 127

    def test_velocity_variation(self):
        """Velocities should vary (not always same)."""
        h = VelocityHumaniser()
        velocities = [h.get_velocity(CH_BASS) for _ in range(10)]
        # Should have some variation
        assert len(set(velocities)) > 1


class TestArpeggioEngine:
    """Test arpeggio pattern engine."""

    def test_engine_initialization(self):
        engine = ArpeggioEngine()
        assert engine.current_chord_name() == "Am"
        assert engine.current_pattern_label() == "A"

    def test_tick_generates_events(self):
        engine = ArpeggioEngine()
        events = engine.tick(120.0)
        assert events is not None
        assert len(events) > 0
        # Each note should have note_on and note_off
        assert len(events) % 2 == 0

    def test_note_on_note_off_pairing(self):
        engine = ArpeggioEngine()
        events = engine.tick(120.0)

        note_ons = [e for e in events if e.kind_priority == 1]
        note_offs = [e for e in events if e.kind_priority == 0]

        assert len(note_ons) > 0
        assert len(note_offs) == len(note_ons)

    def test_note_off_comes_later(self):
        """For each note, note_off time should be > note_on time."""
        engine = ArpeggioEngine()
        events = engine.tick(120.0)

        # Group by note
        notes: dict[int, list] = {}
        for e in events:
            if e.note not in notes:
                notes[e.note] = []
            notes[e.note].append(e)

        for note, note_events in notes.items():
            on_events = [e for e in note_events if e.kind_priority == 1]
            off_events = [e for e in note_events if e.kind_priority == 0]

            if on_events and off_events:
                assert off_events[0].time_ms > on_events[0].time_ms

    def test_chord_changes_every_8_beats(self):
        """Chord should change after 32 sixteenth notes."""
        engine = ArpeggioEngine()

        # Simulate 32 sixteenths (8 beats)
        for _ in range(32):
            engine.tick(120.0)

        # Should have advanced to next chord
        assert engine.current_chord_name() == "Dm"

    def test_pattern_rotates_with_chord(self):
        """Pattern should change when chord changes."""
        engine = ArpeggioEngine()
        initial_pattern = engine.current_pattern_label()

        # Advance through one chord
        for _ in range(32):
            engine.tick(120.0)

        # Pattern should have rotated
        assert engine.current_pattern_label() != initial_pattern

    def test_reset_returns_to_start(self):
        engine = ArpeggioEngine()

        # Advance
        for _ in range(64):
            engine.tick(120.0)

        engine.reset()

        assert engine.current_chord_name() == "Am"
        assert engine.current_pattern_label() == "A"

    def test_valid_midi_channels(self):
        """All events should use valid channels."""
        engine = ArpeggioEngine()

        for _ in range(100):
            events = engine.tick(120.0)
            for ev in events or []:
                assert ev.channel in ALL_CHANNELS

    def test_valid_midi_notes(self):
        """All events should use valid note numbers."""
        engine = ArpeggioEngine()

        for _ in range(100):
            events = engine.tick(120.0)
            for ev in events or []:
                assert 0 <= ev.note <= 127


class TestChannelMapping:
    """Test that notes map to correct channels based on voicing."""

    def test_am_voicing_channels(self):
        am = PROGRESSION[0]
        engine = ArpeggioEngine()
        engine.reset()

        # Get a few events
        for _ in range(4):
            events = engine.tick(120.0)
            for ev in events or []:
                if ev.note in am.bass:
                    assert ev.channel == CH_BASS
                elif ev.note in am.mid:
                    assert ev.channel == CH_MID
                elif ev.note in am.treble:
                    assert ev.channel == CH_TREBLE
