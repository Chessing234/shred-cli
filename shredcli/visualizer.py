"""
ASCII/Terminal visualizer for Shred-CLI.
Provides simple visualization when Rich is not available.
"""

from __future__ import annotations

import sys
import time
import threading
from typing import Optional, Dict, Any


class SimpleVisualizer:
    """Simple ASCII-based visualizer for terminals without Rich."""
    
    # ANSI color codes
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    
    def __init__(self) -> None:
        self._running = False
        self._data: Dict[str, Any] = {
            "bpm": 40.0,
            "wpm": 0.0,
            "chord": "Am",
            "pattern": "A",
            "level": 1,
            "xp": 0,
            "keystrokes": 0,
        }
        self._lock = threading.Lock()
    
    def _color(self, text: str, color: str) -> str:
        """Wrap text in ANSI color codes."""
        if sys.platform == "win32":
            return text  # Windows might not support ANSI
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _draw_bar(self, value: float, max_val: float, width: int = 30) -> str:
        """Draw an ASCII progress bar."""
        filled = int((value / max_val) * width)
        filled = max(0, min(width, filled))
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _get_tempo_color(self, bpm: float) -> str:
        """Get color based on tempo."""
        if bpm < 80:
            return "cyan"
        elif bpm < 120:
            return "green"
        elif bpm < 160:
            return "yellow"
        else:
            return "red"
    
    def _get_tempo_name(self, bpm: float) -> str:
        """Get musical tempo name."""
        if bpm < 80:
            return "Adagio 🐢"
        elif bpm < 120:
            return "Andante 🚶"
        elif bpm < 160:
            return "Allegro 🏃"
        else:
            return "Presto! 🔥"
    
    def render(self) -> str:
        """Render the ASCII dashboard."""
        with self._lock:
            bpm = self._data.get("bpm", 40.0)
            wpm = self._data.get("wpm", 0.0)
            chord = self._data.get("chord", "Am")
            pattern = self._data.get("pattern", "A")
            level = self._data.get("level", 1)
            xp = self._data.get("xp", 0)
            keystrokes = self._data.get("keystrokes", 0)
        
        tempo_color = self._get_tempo_color(bpm)
        
        lines = [
            "",
            self._color("╔═══════════════════════════════════════════════════════════╗", "blue"),
            self._color("║           🎸  SHRED-CLI  v0.2.0  🎸                      ║", "bold"),
            self._color("╚═══════════════════════════════════════════════════════════╝", "blue"),
            "",
            f"  {self._color('♪ Tempo', 'blue')}          {self._color('⌨️ WPM', 'white')}           {self._color('🎸 Guitar', 'magenta')}",
            f"  {self._color(f'{bpm:.1f} BPM', tempo_color)}       {self._color(f'{wpm:.1f}', 'green')}             {self._color(f'Chord: {chord}', 'yellow')}",
            f"  {self._color(self._draw_bar(bpm, 200), tempo_color)}  {self._color(f'Pattern: {pattern}', 'cyan')}",
            f"  {self._color(self._get_tempo_name(bpm), 'dim')}",
            "",
            f"  {self._color('⭐ Progress', 'yellow')}",
            f"  Level {level}  |  XP: {xp}",
            f"  {self._color(self._draw_bar(xp, level * 1000), 'yellow')}",
            "",
            f"  Keystrokes: {keystrokes:,}",
            "",
            self._color("  Press Ctrl+C to stop", "dim"),
            "",
        ]
        
        return "\n".join(lines)
    
    def update(self, **kwargs) -> None:
        """Update visualization data."""
        with self._lock:
            self._data.update(kwargs)
    
    def start(self) -> None:
        """Start the visualizer display loop."""
        self._running = True
        
        try:
            while self._running:
                # Clear screen (cross-platform)
                print("\033[2J\033[H" if sys.platform != "win32" else "\n" * 50)
                print(self.render())
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
    
    def stop(self) -> None:
        """Stop the visualizer."""
        self._running = False


def create_visualizer() -> SimpleVisualizer:
    """Factory function for simple visualizer."""
    return SimpleVisualizer()


# Example usage
if __name__ == "__main__":
    vis = SimpleVisualizer()
    
    # Simulate some data
    import random
    try:
        while True:
            vis.update(
                bpm=random.uniform(40, 180),
                wpm=random.uniform(20, 120),
                keystrokes=int(time.time() * 10) % 10000,
            )
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
