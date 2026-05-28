"""
Built-in software synthesizer for Shred-CLI.
No external MIDI required - generates audio directly using simpleaudio or sounddevice.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable
from enum import Enum
import struct

_HAS_SOUNDDEVICE = False
_HAS_AUDIO = False

try:
    import sounddevice as sd
    import numpy as np

    _HAS_AUDIO = True
    _HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    np = None  # type: ignore
    sd = None  # type: ignore
    try:
        import simpleaudio as sa  # noqa: F401
        import array  # noqa: F401

        _HAS_AUDIO = True
    except ImportError:
        pass


class Waveform(Enum):
    """Available waveform types."""
    SINE = "sine"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"


@dataclass
class Note:
    """A musical note to synthesize."""
    frequency: float
    midi_note: int
    velocity: int  # 0-127
    duration_ms: float
    start_time: float
    channel: int  # 0=bass, 1=mid, 2=treble


@dataclass
class SoundTheme:
    """A sound theme configuration."""
    name: str
    waveform: Waveform
    attack_ms: float
    decay_ms: float
    sustain_level: float
    release_ms: float
    
    # Filter settings
    filter_cutoff: float  # 0-1 normalized
    filter_resonance: float  # 0-1
    
    # Effects
    reverb_amount: float  # 0-1
    chorus_amount: float  # 0-1
    
    # Volume per channel
    channel_volumes: List[float]  # [bass, mid, treble]


# Predefined sound themes
THEMES: Dict[str, SoundTheme] = {
    "classical_guitar": SoundTheme(
        name="Classical Guitar",
        waveform=Waveform.TRIANGLE,
        attack_ms=10.0,
        decay_ms=100.0,
        sustain_level=0.7,
        release_ms=300.0,
        filter_cutoff=0.4,
        filter_resonance=0.2,
        reverb_amount=0.3,
        chorus_amount=0.1,
        channel_volumes=[1.0, 0.8, 0.9],
    ),
    "piano": SoundTheme(
        name="Grand Piano",
        waveform=Waveform.SAWTOOTH,
        attack_ms=5.0,
        decay_ms=50.0,
        sustain_level=0.6,
        release_ms=500.0,
        filter_cutoff=0.6,
        filter_resonance=0.1,
        reverb_amount=0.4,
        chorus_amount=0.0,
        channel_volumes=[1.0, 0.9, 0.85],
    ),
    "synthwave": SoundTheme(
        name="Synthwave",
        waveform=Waveform.SAWTOOTH,
        attack_ms=50.0,
        decay_ms=200.0,
        sustain_level=0.8,
        release_ms=800.0,
        filter_cutoff=0.3,
        filter_resonance=0.5,
        reverb_amount=0.5,
        chorus_amount=0.4,
        channel_volumes=[1.2, 1.0, 1.0],
    ),
    "8bit": SoundTheme(
        name="8-Bit Retro",
        waveform=Waveform.SQUARE,
        attack_ms=0.0,
        decay_ms=0.0,
        sustain_level=1.0,
        release_ms=50.0,
        filter_cutoff=1.0,
        filter_resonance=0.0,
        reverb_amount=0.0,
        chorus_amount=0.0,
        channel_volumes=[1.0, 1.0, 1.0],
    ),
    "pad": SoundTheme(
        name="Ambient Pad",
        waveform=Waveform.SINE,
        attack_ms=500.0,
        decay_ms=500.0,
        sustain_level=0.8,
        release_ms=2000.0,
        filter_cutoff=0.3,
        filter_resonance=0.3,
        reverb_amount=0.7,
        chorus_amount=0.6,
        channel_volumes=[1.3, 1.0, 0.8],
    ),
    "pluck": SoundTheme(
        name="Harp Pluck",
        waveform=Waveform.TRIANGLE,
        attack_ms=2.0,
        decay_ms=30.0,
        sustain_level=0.2,
        release_ms=100.0,
        filter_cutoff=0.7,
        filter_resonance=0.1,
        reverb_amount=0.2,
        chorus_amount=0.0,
        channel_volumes=[0.9, 1.0, 1.1],
    ),
}


# MIDI note number to frequency
NOTE_FREQUENCIES: Dict[int, float] = {
    21: 27.50,  # A0
    22: 29.14,
    23: 30.87,
    24: 32.70,  # C1
    25: 34.65,
    26: 36.71,
    27: 38.89,
    28: 41.20,
    29: 43.65,
    30: 46.25,
    31: 49.00,
    32: 51.91,
    33: 55.00,  # A1
    34: 58.27,
    35: 61.74,
    36: 65.41,  # C2
    37: 69.30,
    38: 73.42,
    39: 77.78,
    40: 82.41,
    41: 87.31,
    42: 92.50,
    43: 98.00,  # G2
    44: 103.83,
    45: 110.00, # A2
    46: 116.54,
    47: 123.47,
    48: 130.81, # C3
    49: 138.59,
    50: 146.83, # D3
    51: 155.56,
    52: 164.81, # E3
    53: 174.61, # F3
    54: 185.00,
    55: 196.00, # G3
    56: 207.65,
    57: 220.00, # A3
    58: 233.08,
    59: 246.94, # B3
    60: 261.63, # C4 (Middle C)
    61: 277.18,
    62: 293.66, # D4
    63: 311.13,
    64: 329.63, # E4
    65: 349.23, # F4
    66: 369.99,
    67: 392.00, # G4
    68: 415.30,
    69: 440.00, # A4
    70: 466.16,
    71: 493.88, # B4
    72: 523.25, # C5
    73: 554.37,
    74: 587.33, # D5
    75: 622.25,
    76: 659.25, # E5
    77: 698.46,
    78: 739.99,
    79: 783.99,
    80: 830.61,
    81: 880.00,
    82: 932.33,
    83: 987.77,
    84: 1046.50,
}


def midi_note_to_freq(note: int) -> float:
    """Convert MIDI note number to frequency."""
    if note in NOTE_FREQUENCIES:
        return NOTE_FREQUENCIES[note]
    # Calculate using formula: f = 440 * 2^((n-69)/12)
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def generate_waveform(freq: float, duration: float, sample_rate: int, 
                      waveform: Waveform, velocity: int) -> List[float]:
    """Generate a basic waveform."""
    samples = int(duration * sample_rate)
    result = []
    vel_norm = velocity / 127.0
    
    for i in range(samples):
        t = i / sample_rate
        phase = 2 * math.pi * freq * t
        
        if waveform == Waveform.SINE:
            sample = math.sin(phase)
        elif waveform == Waveform.SQUARE:
            sample = 1.0 if math.sin(phase) > 0 else -1.0
        elif waveform == Waveform.SAWTOOTH:
            sample = 2.0 * (phase / (2 * math.pi) - math.floor(phase / (2 * math.pi) + 0.5))
        elif waveform == Waveform.TRIANGLE:
            sample = 2.0 * math.asin(math.sin(phase)) / math.pi
        else:
            sample = math.sin(phase)
        
        result.append(sample * vel_norm)
    
    return result


def apply_adsr(samples: List[float], sample_rate: int, 
               attack_ms: float, decay_ms: float, 
               sustain_level: float, release_ms: float) -> List[float]:
    """Apply ADSR envelope to samples."""
    attack_samples = int(attack_ms * sample_rate / 1000)
    decay_samples = int(decay_ms * sample_rate / 1000)
    release_samples = int(release_ms * sample_rate / 1000)
    
    result = []
    total_samples = len(samples)
    
    for i, sample in enumerate(samples):
        # Attack phase
        if i < attack_samples and attack_samples > 0:
            envelope = i / attack_samples
        # Decay phase
        elif i < attack_samples + decay_samples and decay_samples > 0:
            decay_progress = (i - attack_samples) / decay_samples
            envelope = 1.0 - (1.0 - sustain_level) * decay_progress
        # Sustain phase (check if we need to start release)
        elif i < total_samples - release_samples:
            envelope = sustain_level
        # Release phase
        elif release_samples > 0:
            release_progress = (i - (total_samples - release_samples)) / release_samples
            envelope = sustain_level * (1.0 - release_progress)
        else:
            envelope = 0
        
        result.append(sample * envelope)
    
    return result


def apply_lowpass(samples: List[float], cutoff: float, resonance: float) -> List[float]:
    """Simple lowpass filter."""
    if cutoff >= 1.0:
        return samples
    
    result = []
    prev = 0.0
    
    for sample in samples:
        # Simple first-order filter
        output = prev + cutoff * (sample - prev)
        prev = output
        result.append(output)
    
    return result


class SoftSynthesizer:
    """
    Built-in software synthesizer that generates audio directly.
    No external MIDI required!
    """
    
    SAMPLE_RATE = 44100
    BUFFER_SIZE = 1024
    
    def __init__(self, theme: str = "classical_guitar") -> None:
        if not _HAS_AUDIO:
            raise ImportError(
                "SoftSynthesizer requires sounddevice or simpleaudio. "
                "Install: pip install sounddevice numpy"
            )
        
        self.theme = THEMES.get(theme, THEMES["classical_guitar"])
        self._active_notes: List[Note] = []
        self._lock = threading.Lock()
        self._running = False
        self._stream: Optional[sd.OutputStream] = None
        self._audio_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[int, int, int], None]] = None
        
    def set_theme(self, theme: str) -> None:
        """Change the sound theme."""
        self.theme = THEMES.get(theme, THEMES["classical_guitar"])
    
    def note_on(self, channel: int, note: int, velocity: int, duration_ms: float = 500.0) -> None:
        """Trigger a note."""
        freq = midi_note_to_freq(note)
        new_note = Note(
            frequency=freq,
            midi_note=note,
            velocity=velocity,
            duration_ms=duration_ms,
            start_time=time.time(),
            channel=channel,
        )
        
        with self._lock:
            self._active_notes.append(new_note)
            
        if self._callback:
            self._callback(channel, note, velocity)
    
    def note_off(self, channel: int, note: int) -> None:
        """Release a note."""
        with self._lock:
            self._active_notes = [
                n
                for n in self._active_notes
                if not (n.channel == channel and n.midi_note == note)
            ]
    
    def _generate_buffer(self, frames: int):
        """Generate one block of audio samples."""
        if _HAS_SOUNDDEVICE and np is not None:
            buffer = np.zeros(frames, dtype=np.float32)
            
            with self._lock:
                current_time = time.time()
                expired_notes = []
                
                for note in self._active_notes:
                    elapsed = (current_time - note.start_time) * 1000  # ms
                    remaining = note.duration_ms - elapsed
                    
                    if remaining <= 0:
                        expired_notes.append(note)
                        continue
                    
                    # Generate waveform
                    duration = min(remaining / 1000.0, frames / self.SAMPLE_RATE)
                    samples = generate_waveform(
                        note.frequency, duration, self.SAMPLE_RATE, 
                        self.theme.waveform, note.velocity
                    )
                    
                    # Apply ADSR
                    samples = apply_adsr(
                        samples, self.SAMPLE_RATE,
                        self.theme.attack_ms, self.theme.decay_ms,
                        self.theme.sustain_level, self.theme.release_ms
                    )
                    
                    # Apply filter
                    samples = apply_lowpass(
                        samples, self.theme.filter_cutoff, 
                        self.theme.filter_resonance
                    )
                    
                    # Mix into buffer with channel volume
                    volume = self.theme.channel_volumes[note.channel % 3]
                    for i, sample in enumerate(samples):
                        if i < frames:
                            buffer[i] += sample * volume * 0.3  # Prevent clipping
                
                # Remove expired notes
                for note in expired_notes:
                    self._active_notes.remove(note)
            
            buffer = np.clip(buffer, -1.0, 1.0)
            return buffer
        else:
            # simpleaudio fallback
            buffer = [0.0] * frames
            
            with self._lock:
                current_time = time.time()
                expired_notes = []
                
                for note in self._active_notes:
                    elapsed = (current_time - note.start_time) * 1000
                    remaining = note.duration_ms - elapsed
                    
                    if remaining <= 0:
                        expired_notes.append(note)
                        continue
                    
                    duration = min(remaining / 1000.0, frames / self.SAMPLE_RATE)
                    samples = generate_waveform(
                        note.frequency, duration, self.SAMPLE_RATE,
                        self.theme.waveform, note.velocity
                    )
                    
                    samples = apply_adsr(
                        samples, self.SAMPLE_RATE,
                        self.theme.attack_ms, self.theme.decay_ms,
                        self.theme.sustain_level, self.theme.release_ms
                    )
                    
                    volume = self.theme.channel_volumes[note.channel % 3]
                    for i, sample in enumerate(samples):
                        if i < frames:
                            buffer[i] += sample * volume * 0.3
                
                for note in expired_notes:
                    self._active_notes.remove(note)
            
            return [max(-1.0, min(1.0, s)) for s in buffer]
    
    def _audio_callback(self, outdata, frames, time_info, status):
        """Callback for sounddevice."""
        if status:
            print(f"Audio status: {status}")

        data = self._generate_buffer(frames)
        if isinstance(data, list):
            outdata[:, 0] = data[:frames]
        else:
            outdata[:, 0] = data
    
    def start(self) -> None:
        """Start the synthesizer."""
        if not _HAS_AUDIO:
            print("Warning: No audio library available. Install sounddevice or simpleaudio.")
            return
        
        self._running = True
        
        if _HAS_SOUNDDEVICE:
            try:
                self._stream = sd.OutputStream(
                    samplerate=self.SAMPLE_RATE,
                    channels=1,
                    dtype='float32',
                    blocksize=self.BUFFER_SIZE,
                    callback=self._audio_callback,
                )
                self._stream.start()
            except Exception as e:
                print(f"Could not start audio stream: {e}")
                self._running = False
        else:
            # simpleaudio mode - use threading
            self._audio_thread = threading.Thread(target=self._simpleaudio_loop)
            self._audio_thread.daemon = True
            self._audio_thread.start()
    
    def _simpleaudio_loop(self) -> None:
        """Simpleaudio playback loop."""
        while self._running:
            # Generate and play audio in chunks
            time.sleep(0.01)
    
    def stop(self) -> None:
        """Stop the synthesizer."""
        self._running = False
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
    
    def all_notes_off(self) -> None:
        """Stop all playing notes."""
        with self._lock:
            self._active_notes.clear()
    
    @classmethod
    def get_available_themes(cls) -> List[str]:
        """Get list of available sound themes."""
        return list(THEMES.keys())
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if softsynth is available."""
        return _HAS_AUDIO


def create_synthesizer(theme: str = "classical_guitar") -> Optional[SoftSynthesizer]:
    """Factory to create synthesizer if available."""
    if SoftSynthesizer.is_available():
        return SoftSynthesizer(theme)
    return None
