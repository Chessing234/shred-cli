"""
Chord voicings and arpeggio pattern definitions for Shred-CLI.
Voices: bass (strings 6–5), mid (4–3), treble (2–1). MIDI channels 1–3 (0-based in code).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Sequence, Tuple

# Chord progression in Am: i, iv, V, VI, III, VII
# MIDI note numbers as given in the spec (low to high = string 6 → 1).

CHORD_NAMES = ("Am", "Dm", "E7", "F", "C", "G")


@dataclass(frozen=True)
class Voicing:
    """Four-part simulation: bass (2 notes), mid (2), treble (2)."""

    name: str
    bass: Tuple[int, int]
    mid: Tuple[int, int]
    treble: Tuple[int, int]

    def all_notes(self) -> List[int]:
        return list(self.bass + self.mid + self.treble)


def _voicing_am() -> Voicing:
    # Am: [A2, E3, A3, C4, E4, A4]
    return Voicing("Am", (45, 52), (57, 60), (64, 69))


def _voicing_dm() -> Voicing:
    # Dm: [D3, A3, D4, F4, A4] — duplicate high A for treble[1]
    return Voicing("Dm", (50, 57), (62, 65), (69, 69))


def _voicing_e7() -> Voicing:
    # E7: [E3, B3, E4, G#4, B4, D5]
    return Voicing("E7", (52, 59), (64, 68), (71, 74))


def _voicing_f() -> Voicing:
    # F: [F3, C4, F4, A4, C5]
    return Voicing("F", (53, 60), (65, 69), (72, 72))


def _voicing_c() -> Voicing:
    # C: [C3, G3, C4, E4, G4]
    return Voicing("C", (48, 55), (60, 64), (67, 67))


def _voicing_g() -> Voicing:
    # G: [G2, D3, G3, B3, D4]
    return Voicing("G", (43, 50), (55, 59), (62, 62))


PROGRESSION: Tuple[Voicing, ...] = (
    _voicing_am(),
    _voicing_dm(),
    _voicing_e7(),
    _voicing_f(),
    _voicing_c(),
    _voicing_g(),
)

# Pattern labels rotate each chord change
PATTERN_LABELS = ("A", "B", "C", "D", "E")

# MIDI channel index 0,1,2 => user-facing channels 1,2,3 (bass, mid, treble)
CH_BASS = 0
CH_MID = 1
CH_TREBLE = 2

# One arpeggio step: list of (channel, note) played at this 16th subdivision
ArpStep = List[Tuple[int, int]]


def _step(notes: Sequence[Tuple[int, int]]) -> ArpStep:
    return list(notes)


def pattern_a(v: Voicing) -> List[ArpStep]:
    """p i m a: bass[0], mid[0], mid[1], treble[0]"""
    b, m, t = v.bass, v.mid, v.treble
    return [
        _step([(CH_BASS, b[0])]),
        _step([(CH_MID, m[0])]),
        _step([(CH_MID, m[1])]),
        _step([(CH_TREBLE, t[0])]),
    ]


def pattern_b(v: Voicing) -> List[ArpStep]:
    """p a m i: bass[0], treble[0], mid[1], mid[0]"""
    b, m, t = v.bass, v.mid, v.treble
    return [
        _step([(CH_BASS, b[0])]),
        _step([(CH_TREBLE, t[0])]),
        _step([(CH_MID, m[1])]),
        _step([(CH_MID, m[0])]),
    ]


def pattern_c(v: Voicing) -> List[ArpStep]:
    """Alzapúa: bass[0], pinch bass[0]+mid[0], treble[0], mid[1], treble[1]"""
    b, m, t = v.bass, v.mid, v.treble
    return [
        _step([(CH_BASS, b[0])]),
        _step([(CH_BASS, b[0]), (CH_MID, m[0])]),
        _step([(CH_TREBLE, t[0])]),
        _step([(CH_MID, m[1])]),
        _step([(CH_TREBLE, t[1])]),
    ]


def pattern_d(v: Voicing) -> List[ArpStep]:
    """Tremolo: bass then p a m i on treble[0] (four treble strokes)"""
    b, t = v.bass, v.treble
    return [
        _step([(CH_BASS, b[0])]),
        _step([(CH_TREBLE, t[0])]),
        _step([(CH_TREBLE, t[0])]),
        _step([(CH_TREBLE, t[0])]),
        _step([(CH_TREBLE, t[0])]),
    ]


def pattern_e_simple(v: Voicing) -> List[ArpStep]:
    """Strum: sorted by pitch up, then down; channel from voice membership."""
    notes = sorted(set(v.all_notes()))

    def _channel_for_note(note: int) -> int:
        if note in v.bass:
            return CH_BASS
        if note in v.mid:
            return CH_MID
        return CH_TREBLE

    steps: List[ArpStep] = []
    for n in notes:
        steps.append(_step([(_channel_for_note(n), n)]))
    for n in reversed(notes):
        steps.append(_step([(_channel_for_note(n), n)]))
    return steps


# Use simple channel assignment for pattern E
pattern_e = pattern_e_simple  # noqa: E305

PatternFn = Callable[[Voicing], List[ArpStep]]

PATTERN_FUNCTIONS: Tuple[PatternFn, ...] = (
    pattern_a,
    pattern_b,
    pattern_c,
    pattern_d,
    pattern_e,
)


def expand_pattern_to_sixteenths(pattern_steps: List[ArpStep], total_sixteenths: int = 32) -> List[ArpStep]:
    """
    Repeat the pattern cycle until exactly `total_sixteenths` steps (one chord = 8 beats = 32 sixteenths).
    If the pattern length does not divide 32, truncate the last partial cycle.
    """
    if not pattern_steps:
        return []
    out: List[ArpStep] = []
    i = 0
    while len(out) < total_sixteenths:
        out.append(pattern_steps[i % len(pattern_steps)])
        i += 1
    return out[:total_sixteenths]
