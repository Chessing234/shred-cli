"""
Real-time TUI Dashboard for Shred-CLI using Rich.
Provides beautiful visualization of typing stats, BPM, and achievements.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.table import Table
    from rich.layout import Layout
    from rich.text import Text
    from rich.console import Console
    from rich.align import Align
    from rich.syntax import Syntax
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


@dataclass
class DashboardState:
    """Current state for the dashboard."""
    bpm: float = 40.0
    wpm: float = 0.0
    chord: str = "Am"
    pattern: str = "A"
    uptime_seconds: float = 0.0
    total_keystrokes: int = 0
    session_high_wpm: float = 0.0
    achievements: List[str] = field(default_factory=list)
    recent_chords: List[str] = field(default_factory=list)
    is_typing: bool = False
    current_streak: int = 0
    level: int = 1
    xp: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bpm": self.bpm,
            "wpm": self.wpm,
            "chord": self.chord,
            "pattern": self.pattern,
            "uptime": self.uptime_seconds,
            "keystrokes": self.total_keystrokes,
            "high_wpm": self.session_high_wpm,
            "level": self.level,
            "xp": self.xp,
            "streak": self.current_streak,
        }


class ShredDashboard:
    """
    Rich-based terminal dashboard for Shred-CLI.
    Displays real-time typing metrics, BPM visualization, and achievements.
    """
    
    def __init__(self) -> None:
        if not _HAS_RICH:
            raise ImportError(
                "Rich library required for dashboard. "
                "Install with: pip install rich"
            )
        
        self.console = Console()
        self.state = DashboardState()
        self._lock = threading.Lock()
        self._running = False
        self._live: Optional[Live] = None
        
        # Color schemes based on tempo
        self.tempo_colors = {
            "adagio": "cyan",      # 40-80 BPM
            "andante": "green",    # 80-120 BPM
            "allegro": "yellow",   # 120-160 BPM
            "presto": "red",       # 160-200 BPM
        }
    
    def _get_tempo_color(self, bpm: float) -> str:
        """Get color based on current tempo."""
        if bpm < 80:
            return self.tempo_colors["adagio"]
        elif bpm < 120:
            return self.tempo_colors["andante"]
        elif bpm < 160:
            return self.tempo_colors["allegro"]
        else:
            return self.tempo_colors["presto"]
    
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
    
    def _create_bpm_gauge(self) -> Panel:
        """Create a visual BPM gauge."""
        color = self._get_tempo_color(self.state.bpm)
        progress = (self.state.bpm - 40) / 160  # Normalize 40-200 range
        progress = max(0, min(1, progress))
        
        filled = int(progress * 30)
        empty = 30 - filled
        
        bar = "█" * filled + "░" * empty
        
        content = Text()
        content.append(f"{self.state.bpm:.1f} BPM\n", style=f"bold {color}")
        content.append(f"[{bar}]\n", style=color)
        content.append(f"{self._get_tempo_name(self.state.bpm)}", style=f"dim {color}")
        
        return Panel(
            Align.center(content),
            title="[bold blue]♪ Tempo ♪[/bold blue]",
            border_style=color,
            box=box.ROUNDED
        )
    
    def _create_wpm_panel(self) -> Panel:
        """Create WPM display panel."""
        color = "green" if self.state.wpm > 60 else "yellow" if self.state.wpm > 30 else "dim"
        
        content = Text()
        content.append(f"{self.state.wpm:.1f}\n", style=f"bold {color}")
        content.append("WPM\n", style="dim")
        content.append(f"Session High: {self.state.session_high_wpm:.1f}", style="cyan")
        
        return Panel(
            Align.center(content),
            title="[bold]⌨️ Typing Speed[/bold]",
            border_style=color,
            box=box.ROUNDED
        )
    
    def _create_music_panel(self) -> Panel:
        """Create music/chord display panel."""
        color = self._get_tempo_color(self.state.bpm)
        
        content = Text()
        content.append(f"Chord: ", style="dim")
        content.append(f"{self.state.chord}\n", style=f"bold {color}")
        content.append(f"Pattern: ", style="dim")
        content.append(f"{self.state.pattern}\n", style=f"bold {color}")
        
        # Pattern descriptions
        patterns = {
            "A": "p-i-m-a (classical)",
            "B": "p-a-m-i (reverse)",
            "C": "Alzapúa (flamenco)",
            "D": "Tremolo (rapid)",
            "E": "Rasgueado (strum)",
        }
        content.append(f"\n{patterns.get(self.state.pattern, 'Unknown')}", style="dim")
        
        return Panel(
            Align.center(content),
            title="[bold magenta]🎸 Guitar[/bold magenta]",
            border_style=color,
            box=box.ROUNDED
        )
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        uptime = self._format_time(self.state.uptime_seconds)
        
        content = Text()
        content.append(f"Uptime: {uptime}\n", style="dim")
        content.append(f"Keystrokes: {self.state.total_keystrokes:,}\n", style="cyan")
        content.append(f"Current Streak: {self.state.current_streak}", style="yellow")
        
        return Panel(
            Align.center(content),
            title="[bold]📊 Session Stats[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )
    
    def _create_level_panel(self) -> Panel:
        """Create level/Xp panel."""
        xp_for_next = self.state.level * 1000
        progress = self.state.xp / xp_for_next
        filled = int(progress * 20)
        bar = "█" * filled + "░" * (20 - filled)
        
        content = Text()
        content.append(f"Level {self.state.level}\n", style="bold yellow")
        content.append(f"XP: {self.state.xp}/{xp_for_next}\n", style="dim")
        content.append(f"[{bar}] {int(progress*100)}%", style="green")
        
        return Panel(
            Align.center(content),
            title="[bold yellow]⭐ Progress[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def _create_achievements_panel(self) -> Panel:
        """Create achievements panel."""
        if not self.state.achievements:
            content = Text("No achievements yet...\n", style="dim")
            content.append("Start typing to unlock! 🏆", style="dim italic")
        else:
            content = Text()
            for ach in self.state.achievements[-5:]:  # Show last 5
                content.append(f"🏆 {ach}\n", style="yellow")
        
        return Panel(
            content,
            title=f"[bold gold]🏆 Achievements ({len(self.state.achievements)})[/bold gold]",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def _create_chord_history(self) -> Panel:
        """Create chord progression history."""
        if not self.state.recent_chords:
            content = Text("Waiting for music...", style="dim italic")
        else:
            content = Text(" → ".join(self.state.recent_chords[-8:]), style="cyan")
        
        return Panel(
            Align.center(content),
            title="[bold blue]🎵 Progression[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        )
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS."""
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def _generate_layout(self) -> Layout:
        """Generate the full dashboard layout."""
        layout = Layout()
        
        # Split into header, main, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=5),
        )
        
        # Header with title
        title = Text()
        title.append("╔══════════════════════════════════════════╗\n", style="blue")
        title.append("║     ", style="blue")
        title.append("SHRED-CLI", style="bold red")
        title.append("  🎸 Type Fast, Shred Harder!    ", style="bold")
        title.append("║\n", style="blue")
        title.append("╚══════════════════════════════════════════╝", style="blue")
        
        layout["header"].update(Panel(
            Align.center(title),
            box=box.SIMPLE
        ))
        
        # Main area - split into left/right
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1),
        )
        
        # Left side - metrics
        layout["left"].split_column(
            Layout(name="top_metrics"),
            Layout(name="middle_metrics"),
            Layout(name="history"),
        )
        
        # Top metrics - BPM, WPM, Music
        layout["left"]["top_metrics"].split_row(
            Layout(self._create_bpm_gauge()),
            Layout(self._create_wpm_panel()),
            Layout(self._create_music_panel()),
        )
        
        # Middle - stats and level
        layout["left"]["middle_metrics"].split_row(
            Layout(self._create_stats_panel()),
            Layout(self._create_level_panel()),
        )
        
        # Chord history
        layout["left"]["history"].update(self._create_chord_history())
        
        # Right side - achievements
        layout["right"].update(self._create_achievements_panel())
        
        # Footer - help text
        help_text = Text()
        help_text.append("[Ctrl+C] ", style="bold")
        help_text.append("Stop  ", style="dim")
        help_text.append("|  Type faster ", style="dim")
        help_text.append("→ ", style="dim")
        help_text.append("Higher BPM ", style="green")
        help_text.append("→ ", style="dim")
        help_text.append("Epic shredding! ", style="red")
        help_text.append("🔥", style="yellow")
        
        layout["footer"].update(Panel(
            Align.center(help_text),
            box=box.SIMPLE
        ))
        
        return layout
    
    def update(self, **kwargs) -> None:
        """Update dashboard state."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            
            # Track session high WPM
            if self.state.wpm > self.state.session_high_wpm:
                self.state.session_high_wpm = self.state.wpm
            
            # Update chord history
            if self.state.chord not in self.state.recent_chords[-1:]:
                self.state.recent_chords.append(self.state.chord)
                if len(self.state.recent_chords) > 10:
                    self.state.recent_chords = self.state.recent_chords[-10:]
    
    def refresh(self) -> None:
        """Force refresh the display."""
        if self._live:
            self._live.update(self._generate_layout())
    
    def start(self) -> None:
        """Start the dashboard display."""
        if not _HAS_RICH:
            print("Dashboard requires 'rich' library. Install: pip install rich")
            return
        
        self._running = True
        self.console.clear()
        
        with Live(
            self._generate_layout(),
            console=self.console,
            refresh_per_second=4,
            screen=True,
        ) as live:
            self._live = live
            try:
                while self._running:
                    time.sleep(0.25)
                    with self._lock:
                        live.update(self._generate_layout())
            except KeyboardInterrupt:
                pass
            finally:
                self._running = False
    
    def stop(self) -> None:
        """Stop the dashboard."""
        self._running = False
    
    def add_achievement(self, achievement: str) -> None:
        """Add an achievement to display."""
        with self._lock:
            if achievement not in self.state.achievements:
                self.state.achievements.append(achievement)
                # Flash notification
                if self._live:
                    self.console.print(
                        f"\n🎉 ACHIEVEMENT UNLOCKED: {achievement}\n",
                        style="bold yellow on black"
                    )


def create_simple_dashboard() -> Optional[ShredDashboard]:
    """Factory function to create dashboard if Rich is available."""
    if _HAS_RICH:
        return ShredDashboard()
    return None
