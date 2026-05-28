"""
MIDI recording and export functionality for Shred-CLI.
Records sessions to MIDI files and provides playback capabilities.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import deque

try:
    import mido
    from mido import Message, MidiFile, MidiTrack, MetaMessage
    _HAS_MIDO = True
except ImportError:
    _HAS_MIDO = False


@dataclass
class MidiEvent:
    """A single MIDI event for recording."""
    timestamp: float  # Absolute time in seconds
    message_type: str  # note_on, note_off, control_change, etc.
    channel: int
    note: int
    velocity: int
    delta_time: float = 0.0  # Time since last event (for MIDI file)


@dataclass  
class RecordingSession:
    """A complete recorded session."""
    start_time: float
    end_time: Optional[float] = None
    events: List[MidiEvent] = field(default_factory=list)
    bpm_changes: Dict[float, float] = field(default_factory=dict)  # time -> BPM
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def duration(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def event_count(self) -> int:
        """Get total number of MIDI events."""
        return len(self.events)
    
    def note_count(self) -> int:
        """Get number of note_on events."""
        return sum(1 for e in self.events if e.message_type == "note_on")


class MidiRecorder:
    """
    Records MIDI events to memory and optionally exports to file.
    """
    
    DATA_DIR = Path.home() / ".shredcli" / "recordings"
    
    def __init__(self) -> None:
        if not _HAS_MIDO:
            raise ImportError("MidiRecorder requires mido. Install: pip install mido")
        
        self._current_session: Optional[RecordingSession] = None
        self._sessions: deque[RecordingSession] = deque(maxlen=50)  # Keep last 50
        self._recording = False
        self._lock = threading.Lock()
        self._last_event_time: float = 0.0
        
        # Ensure directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def start_recording(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a new recording session."""
        with self._lock:
            self._current_session = RecordingSession(
                start_time=time.time(),
                metadata=metadata or {},
            )
            self._recording = True
            self._last_event_time = time.time()
    
    def stop_recording(self) -> Optional[RecordingSession]:
        """Stop current recording and return the session."""
        with self._lock:
            if self._current_session and self._recording:
                self._current_session.end_time = time.time()
                self._recording = False
                session = self._current_session
                self._sessions.append(session)
                self._current_session = None
                return session
            return None
    
    def record_event(self, message_type: str, channel: int, 
                     note: int, velocity: int) -> None:
        """Record a MIDI event."""
        with self._lock:
            if not self._recording or not self._current_session:
                return
            
            now = time.time()
            delta = now - self._last_event_time
            self._last_event_time = now
            
            event = MidiEvent(
                timestamp=now,
                message_type=message_type,
                channel=channel,
                note=note,
                velocity=velocity,
                delta_time=delta,
            )
            self._current_session.events.append(event)
    
    def record_bpm_change(self, bpm: float) -> None:
        """Record a BPM change."""
        with self._lock:
            if self._current_session and self._recording:
                self._current_session.bpm_changes[time.time()] = bpm
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self._recording
    
    def export_to_midi(self, session: RecordingSession, 
                       filepath: Optional[Path] = None) -> Path:
        """
        Export a recorded session to a standard MIDI file.
        
        Args:
            session: The session to export
            filepath: Output path (default: auto-generated in recordings dir)
        
        Returns:
            Path to the saved MIDI file
        """
        if not _HAS_MIDO:
            raise RuntimeError("mido required for MIDI export")
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"shred_session_{timestamp}.mid"
            filepath = self.DATA_DIR / filename
        
        mid = MidiFile(ticks_per_beat=480)
        ticks_per_beat = mid.ticks_per_beat
        default_bpm = 120.0

        tempo_track = MidiTrack()
        tempo_track.append(MetaMessage("track_name", name="Shred-CLI Session", time=0))
        tempo_track.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(default_bpm), time=0))
        mid.tracks.append(tempo_track)

        tracks: Dict[int, MidiTrack] = {}
        for ch in range(3):
            track = MidiTrack()
            mid.tracks.append(track)
            tracks[ch] = track
            names = ["Bass (6-5)", "Mid (4-3)", "Treble (2-1)"]
            track.append(MetaMessage("track_name", name=names[ch], time=0))

        sorted_events = sorted(session.events, key=lambda e: e.timestamp)
        if not sorted_events:
            mid.save(str(filepath))
            return filepath

        session_start = session.start_time
        last_abs_tick = 0

        for event in sorted_events:
            if event.channel not in tracks:
                continue

            abs_seconds = max(0.0, event.timestamp - session_start)
            abs_ticks = int(abs_seconds * ticks_per_beat * default_bpm / 60.0)
            delta_ticks = max(0, abs_ticks - last_abs_tick)
            if delta_ticks == 0 and event.message_type == "note_off":
                delta_ticks = 60  # ~1/8 beat at 120 BPM when events share a timestamp
            last_abs_tick = last_abs_tick + delta_ticks

            track = tracks[event.channel]
            if event.message_type == "note_on":
                track.append(
                    Message(
                        "note_on",
                        channel=event.channel,
                        note=event.note,
                        velocity=max(1, min(127, event.velocity)),
                        time=delta_ticks,
                    )
                )
            elif event.message_type == "note_off":
                track.append(
                    Message(
                        "note_off",
                        channel=event.channel,
                        note=event.note,
                        velocity=0,
                        time=delta_ticks,
                    )
                )

        for track in mid.tracks[1:]:
            track.append(MetaMessage("end_of_track", time=0))
        tempo_track.append(MetaMessage("end_of_track", time=0))
        
        # Save file
        mid.save(str(filepath))
        return filepath
    
    def get_sessions(self) -> List[RecordingSession]:
        """Get all stored recording sessions."""
        with self._lock:
            return list(self._sessions)
    
    def get_session_summary(self) -> List[Dict[str, Any]]:
        """Get summaries of all sessions."""
        summaries = []
        for i, session in enumerate(self._sessions):
            summaries.append({
                "index": i,
                "date": datetime.fromtimestamp(session.start_time).isoformat(),
                "duration_seconds": session.duration(),
                "event_count": session.event_count(),
                "note_count": session.note_count(),
                "metadata": session.metadata,
            })
        return list(reversed(summaries))  # Most recent first
    
    def delete_session(self, index: int) -> bool:
        """Delete a session by index."""
        with self._lock:
            sessions_list = list(self._sessions)
            if 0 <= index < len(sessions_list):
                del sessions_list[index]
                self._sessions.clear()
                self._sessions.extend(sessions_list)
                return True
            return False
    
    def auto_save(self) -> Optional[Path]:
        """Automatically save current session if it has enough content."""
        if self._current_session and len(self._current_session.events) > 50:
            return self.export_to_midi(self._current_session)
        return None


class SessionPlayer:
    """
    Plays back recorded MIDI sessions.
    """
    
    def __init__(self, output_callback: Optional[Any] = None) -> None:
        self._output_callback = output_callback
        self._playing = False
        self._stop_requested = threading.Event()
    
    def play_session(self, session: RecordingSession, 
                     speed_factor: float = 1.0) -> None:
        """
        Play back a recorded session.
        
        Args:
            session: Session to play
            speed_factor: Playback speed (1.0 = normal, 2.0 = double speed)
        """
        if not session.events:
            return
        
        self._playing = True
        self._stop_requested.clear()
        
        start_time = time.time()
        first_event_time = session.events[0].timestamp
        
        for event in session.events:
            if self._stop_requested.is_set():
                break
            
            # Calculate when this event should occur
            event_time = (event.timestamp - first_event_time) / speed_factor
            current_time = time.time() - start_time
            
            # Wait if needed
            if event_time > current_time:
                wait_time = event_time - current_time
                time.sleep(wait_time)
            
            # Send event to callback
            if self._output_callback:
                self._output_callback(
                    event.message_type,
                    event.channel,
                    event.note,
                    event.velocity
                )
        
        self._playing = False
    
    def stop(self) -> None:
        """Stop playback."""
        self._stop_requested.set()
        self._playing = False
    
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._playing


# Global recorder instance
_recorder: Optional[MidiRecorder] = None


def get_recorder() -> MidiRecorder:
    """Get or create global MIDI recorder."""
    global _recorder
    if _recorder is None:
        _recorder = MidiRecorder()
    return _recorder
