"""
MIDI playback thread, arpeggio engine, scheduler, and velocity humanisation.
"""

from __future__ import annotations

import heapq
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

NoteCallback = Callable[[int, int, int], None]
NoteOffCallback = Callable[[int, int], None]

import mido

from shredcli.theory import (
    CH_BASS,
    CH_MID,
    CH_TREBLE,
    PROGRESSION,
    PATTERN_FUNCTIONS,
    PATTERN_LABELS,
    Voicing,
    expand_pattern_to_sixteenths,
)

ALL_CHANNELS = (0, 1, 2)  # 0-based; user-facing 1,2,3
DRUM_CHANNEL = 9  # 0-based; user sees channel 10


@dataclass(order=True)
class MidiEvent:
    """
    Scheduled MIDI event.
    Sort by (time_ms, kind_priority) where kind_priority ensures note_off before note_on at same time.
    """

    time_ms: float = field(compare=True)
    kind_priority: int = field(compare=True)  # 0=note_off, 1=note_on
    channel: int = field(compare=False)
    note: int = field(compare=False)
    velocity: int = field(compare=False)


class VelocityHumaniser:
    """
    Per-note velocity based on voice with ±10 jitter clamped to 1–127.
    Bass: 90–110, Mid: 60–80, Treble: 70–95
    """

    def __init__(self) -> None:
        self._ranges: dict[int, Tuple[int, int]] = {
            CH_BASS: (90, 110),
            CH_MID: (60, 80),
            CH_TREBLE: (70, 95),
        }
        self._lock = threading.Lock()

    def get_velocity(self, channel: int) -> int:
        low, high = self._ranges.get(channel, (70, 95))
        base = random.randint(low, high)
        jitter = random.randint(-10, 10)
        with self._lock:
            return max(1, min(127, base + jitter))


class ArpeggioEngine:
    """
    Cycles through the progression, advancing chord every 8 beats (32 sixteenths).
    Rotates patterns each chord change.
    """

    def __init__(self) -> None:
        self._chord_index = 0
        self._pattern_index = 0
        self._beats_elapsed = 0  # 0..7 within the chord
        self._sixteenth_in_beat = 0  # 0..3 within beat
        self._sequence_sixteenth_index = 0  # 0..31 within chord
        self._lock = threading.Lock()
        self._humaniser = VelocityHumaniser()

    def tick(self, current_chord_bpm: float) -> Optional[List[MidiEvent]]:
        """
        Advance one sixteenth note; schedule note_on/note_off events.
        Return list of events to enqueue at current time.
        """
        with self._lock:
            voicing = PROGRESSION[self._chord_index]
            pattern_fn = PATTERN_FUNCTIONS[self._pattern_index]
            steps = expand_pattern_to_sixteenths(pattern_fn(voicing), total_sixteenths=32)
            step = steps[self._sequence_sixteenth_index]

            # Build note_on events; note_off will be scheduled 90% of sixteenth duration later
            # Beat duration in ms at this BPM:
            beat_ms = 60000.0 / max(1.0, current_chord_bpm)
            sixteenth_ms = beat_ms / 4.0
            note_dur_ms = sixteenth_ms * 0.9

            now_ms = time.monotonic() * 1000.0
            events: List[MidiEvent] = []
            for ch, note in step:
                vel = self._humaniser.get_velocity(ch)
                events.append(
                    MidiEvent(
                        time_ms=now_ms,
                        kind_priority=1,
                        channel=ch,
                        note=note,
                        velocity=vel,
                    )
                )
                events.append(
                    MidiEvent(
                        time_ms=now_ms + note_dur_ms,
                        kind_priority=0,
                        channel=ch,
                        note=note,
                        velocity=0,
                    )
                )

            # Advance counters
            self._sixteenth_in_beat = (self._sixteenth_in_beat + 1) % 4
            if self._sixteenth_in_beat == 0:
                self._beats_elapsed = (self._beats_elapsed + 1) % 8
                if self._beats_elapsed == 0:
                    # Chord change
                    self._chord_index = (self._chord_index + 1) % len(PROGRESSION)
                    self._pattern_index = (self._pattern_index + 1) % len(PATTERN_FUNCTIONS)
            self._sequence_sixteenth_index = (self._sequence_sixteenth_index + 1) % 32

            return events

    def current_chord_name(self) -> str:
        with self._lock:
            return PROGRESSION[self._chord_index].name

    def current_pattern_label(self) -> str:
        with self._lock:
            return PATTERN_LABELS[self._pattern_index]

    def reset(self) -> None:
        with self._lock:
            self._chord_index = 0
            self._pattern_index = 0
            self._beats_elapsed = 0
            self._sixteenth_in_beat = 0
            self._sequence_sixteenth_index = 0


class MidiPlayerThread(threading.Thread):
    """
    Runs a 10 ms tick loop; maintains a priority queue of scheduled MIDI events.
    Sends note_on/note_off via mido Output.
    Handles BPM changes by stretching remaining event times proportionally.
    """

    def __init__(
        self,
        port_name: str,
        open_port_name: Optional[str] = None,
        *,
        use_midi_output: bool = True,
        on_note_on: Optional[NoteCallback] = None,
        on_note_off: Optional[NoteOffCallback] = None,
    ) -> None:
        super().__init__(name="ShredMidiPlayer", daemon=True)
        self._port_name = port_name
        self._open_port_name = open_port_name
        self._use_midi_output = use_midi_output
        self._on_note_on = on_note_on
        self._on_note_off = on_note_off
        self._output: Optional[mido.Output] = None
        self._queue: List[MidiEvent] = []
        self._queue_lock = threading.Lock()
        self._running = False
        self._stop_event = threading.Event()
        self._tick_ms = 10.0
        self._engine = ArpeggioEngine()
        self._current_bpm = 80.0
        self._bpm_lock = threading.Lock()
        self._beat_ms: float = 60000.0 / self._current_bpm
        self._sixteenth_ms: float = self._beat_ms / 4.0
        self._sixteenth_counter = 0.0  # accumulator for sixteenth timing

    def _try_open_port(self) -> mido.Output:
        try:
            if self._open_port_name:
                return mido.open_output(self._open_port_name)
            ports = mido.get_output_names()
            if not ports:
                raise RuntimeError("No MIDI output ports available.")
            # Prefer a virtual port name that includes our target
            for p in ports:
                if self._port_name.lower() in p.lower():
                    return mido.open_output(p)
            # Otherwise, open the first available
            return mido.open_output(ports[0])
        except Exception as e:
            raise RuntimeError(f"Failed to open MIDI output: {e}") from e

    def _all_notes_off(self) -> None:
        if not self._output:
            return
        for ch in ALL_CHANNELS:
            self._output.send(mido.Message("control_change", channel=ch, control=123, value=0))

    def set_bpm(self, bpm: float) -> None:
        """
        Update BPM and reschedule remaining events proportionally.
        """
        with self._bpm_lock:
            old_beat_ms = 60000.0 / self._current_bpm
            new_beat_ms = 60000.0 / max(1.0, bpm)
            self._current_bpm = bpm
            self._beat_ms = new_beat_ms
            self._sixteenth_ms = new_beat_ms / 4.0

        # Stretch existing events proportionally to new beat duration
        now_ms = time.monotonic() * 1000.0
        with self._queue_lock:
            if self._queue:
                # Rebuild queue with adjusted times
                adjusted: List[MidiEvent] = []
                for ev in self._queue:
                    if ev.time_ms > now_ms:
                        # Scale remaining time proportionally
                        remaining = ev.time_ms - now_ms
                        if old_beat_ms > 0:
                            ratio = new_beat_ms / old_beat_ms
                        else:
                            ratio = 1.0
                        new_time = now_ms + remaining * ratio
                        adjusted.append(
                            MidiEvent(
                                time_ms=new_time,
                                kind_priority=ev.kind_priority,
                                channel=ev.channel,
                                note=ev.note,
                                velocity=ev.velocity,
                            )
                        )
                    else:
                        adjusted.append(ev)
                heapq.heapify(adjusted)
                self._queue = adjusted

    def get_bpm(self) -> float:
        with self._bpm_lock:
            return self._current_bpm

    def current_chord_and_pattern(self) -> Tuple[str, str]:
        return (self._engine.current_chord_name(), self._engine.current_pattern_label())

    def enqueue(self, events: Sequence[MidiEvent]) -> None:
        with self._queue_lock:
            for ev in events:
                heapq.heappush(self._queue, ev)

    def _process_queue(self) -> None:
        now_ms = time.monotonic() * 1000.0
        with self._queue_lock:
            while self._queue and self._queue[0].time_ms <= now_ms:
                ev = heapq.heappop(self._queue)
                msg_type = "note_on" if ev.kind_priority == 1 else "note_off"
                vel = ev.velocity if ev.kind_priority == 1 else 0
                if self._output:
                    try:
                        self._output.send(
                            mido.Message(msg_type, channel=ev.channel, note=ev.note, velocity=vel)
                        )
                    except Exception:
                        pass
                try:
                    if ev.kind_priority == 1 and self._on_note_on:
                        self._on_note_on(ev.channel, ev.note, vel)
                    elif ev.kind_priority == 0 and self._on_note_off:
                        self._on_note_off(ev.channel, ev.note)
                except Exception:
                    pass

    def _advance_sixteenth(self) -> None:
        # Accumulate time; when we cross sixteenth boundary, generate next arpeggio step
        self._sixteenth_counter += self._tick_ms
        with self._bpm_lock:
            threshold = self._sixteenth_ms
        if self._sixteenth_counter >= threshold:
            self._sixteenth_counter = 0.0
            events = self._engine.tick(self.get_bpm())
            if events:
                self.enqueue(events)

    def run(self) -> None:
        if self._use_midi_output:
            try:
                self._output = self._try_open_port()
            except RuntimeError:
                if not (self._on_note_on or self._on_note_off):
                    raise
        self._engine.reset()
        self._running = True
        while not self._stop_event.is_set():
            self._advance_sixteenth()
            self._process_queue()
            time.sleep(self._tick_ms / 1000.0)
        self._all_notes_off()
        if self._output:
            try:
                self._output.close()
            except Exception:
                pass
        self._running = False

    def stop(self) -> None:
        self._stop_event.set()
        self.join(timeout=5.0)
        self._all_notes_off()

    def is_running(self) -> bool:
        return self._running
