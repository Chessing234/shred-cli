"""Tests for built-in synthesizer."""

import pytest

from shredcli.synthesizer import (
    THEMES,
    SoftSynthesizer,
    Waveform,
    generate_waveform,
    midi_note_to_freq,
    apply_adsr,
)


class TestMidiNoteToFreq:
    def test_middle_c(self):
        assert midi_note_to_freq(60) == pytest.approx(261.63, rel=1e-3)

    def test_formula_for_unknown_note(self):
        assert midi_note_to_freq(69) == pytest.approx(440.0, rel=1e-3)


class TestWaveformGeneration:
    def test_sine_length(self):
        samples = generate_waveform(440.0, 0.1, 44100, Waveform.SINE, 100)
        assert len(samples) == 4410

    def test_different_waveforms_differ(self):
        sine = generate_waveform(440.0, 0.01, 44100, Waveform.SINE, 100)
        square = generate_waveform(440.0, 0.01, 44100, Waveform.SQUARE, 100)
        assert sine != square


class TestThemes:
    def test_all_themes_have_distinct_waveforms(self):
        waveforms = {t.waveform for t in THEMES.values()}
        assert len(waveforms) >= 3

    def test_synthwave_vs_8bit(self):
        assert THEMES["synthwave"].waveform != THEMES["8bit"].waveform


@pytest.mark.skipif(not SoftSynthesizer.is_available(), reason="sounddevice/numpy not installed")
class TestSoftSynthesizer:
    def test_start_stop(self):
        synth = SoftSynthesizer("piano")
        synth.start()
        synth.note_on(0, 60, 100, 100)
        synth._generate_buffer(512)
        synth.note_off(0, 60)
        synth.stop()

    def test_theme_changes_waveform(self):
        a = SoftSynthesizer("classical_guitar")
        b = SoftSynthesizer("8bit")
        assert a.theme.waveform != b.theme.waveform

    def test_note_off_removes_note(self):
        synth = SoftSynthesizer("pluck")
        synth.note_on(1, 64, 90, 500)
        assert len(synth._active_notes) == 1
        synth.note_off(1, 64)
        assert len(synth._active_notes) == 0


class TestAdsr:
    def test_envelope_shapes_amplitude(self):
        raw = [1.0] * 1000
        env = apply_adsr(raw, 44100, 10, 50, 0.5, 200)
        assert max(env) > 0
        assert min(env) < max(env)
