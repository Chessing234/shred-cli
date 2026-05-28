"""Tests for MIDI player callback routing."""

import time
from unittest.mock import patch

from shredcli.player import MidiPlayerThread


class TestPlayerCallbacks:
    @patch.object(MidiPlayerThread, "_try_open_port")
    def test_callbacks_without_midi_output(self, mock_open):
        events = []

        def on_on(ch, note, vel):
            events.append(("on", ch, note, vel))

        def on_off(ch, note):
            events.append(("off", ch, note))

        player = MidiPlayerThread(
            port_name="ShredCLI",
            use_midi_output=False,
            on_note_on=on_on,
            on_note_off=on_off,
        )
        player.start()
        time.sleep(0.5)
        player.stop()
        assert any(e[0] == "on" for e in events)
