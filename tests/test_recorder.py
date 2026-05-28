"""Tests for MIDI recorder and export."""

import tempfile
import time
from pathlib import Path

import pytest

try:
    import mido

    _HAS_MIDO = True
except ImportError:
    _HAS_MIDO = False

from shredcli.recorder import MidiRecorder, RecordingSession


@pytest.mark.skipif(not _HAS_MIDO, reason="mido not installed")
class TestMidiRecorder:
    def test_record_and_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = MidiRecorder()
            rec.DATA_DIR = Path(tmpdir)
            rec.start_recording()
            rec.record_event("note_on", 0, 60, 100)
            time.sleep(0.05)
            rec.record_event("note_off", 0, 60, 0)
            session = rec.stop_recording()
            assert session is not None
            assert session.note_count() == 1

            path = rec.export_to_midi(session)
            assert path.exists()
            loaded = mido.MidiFile(str(path))
            assert len(loaded.tracks) >= 2
            assert loaded.length > 0

    def test_session_summary(self):
        rec = MidiRecorder()
        rec.start_recording()
        rec.record_event("note_on", 1, 64, 80)
        rec.stop_recording()
        summaries = rec.get_session_summary()
        assert len(summaries) == 1
