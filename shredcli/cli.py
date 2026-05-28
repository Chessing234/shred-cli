"""
Shred-CLI: Type fast, shred harder - A MIDI-generating typing companion.
Enhanced with analytics, gamification, dashboard, and built-in synthesizer.

CLI entry point using Click.
Commands: start, stop, status, dashboard, stats, export, themes, demo
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional
import json

import click

from shredcli.daemon import (
    DaemonRunner,
    get_status,
    stop_daemon,
    ensure_dirs,
    read_status,
    write_status,
)
from shredcli.listener import AutoSlowdown, KeyListener, WpmCalculator, WpmSmoother
from shredcli.player import MidiPlayerThread, ALL_CHANNELS
from shredcli.theory import PROGRESSION

# Optional imports for hackathon features
try:
    from shredcli.dashboard import create_simple_dashboard, ShredDashboard
    _HAS_DASHBOARD = True
except ImportError:
    _HAS_DASHBOARD = False

try:
    from shredcli.analytics import get_analytics, AnalyticsTracker
    _HAS_ANALYTICS = True
except ImportError:
    _HAS_ANALYTICS = False

try:
    from shredcli.synthesizer import create_synthesizer, SoftSynthesizer, THEMES
    _HAS_SYNTH = True
except ImportError:
    _HAS_SYNTH = False

try:
    from shredcli.recorder import get_recorder, MidiRecorder
    _HAS_RECORDER = True
except ImportError:
    _HAS_RECORDER = False

try:
    import mido
    import mido.backends.backend as mido_backend
    import mido.backends.rtmidi

    _HAS_MIDO = True
except ImportError:
    _HAS_MIDO = False

# Global references for foreground mode
_wpm_calc: Optional[WpmCalculator] = None
_wpm_smoother: Optional[WpmSmoother] = None
_auto_slow: Optional[AutoSlowdown] = None
_player: Optional[MidiPlayerThread] = None
_listener: Optional[KeyListener] = None
_dashboard: Optional['ShredDashboard'] = None
_synth: Optional['SoftSynthesizer'] = None
_analytics: Optional['AnalyticsTracker'] = None
_recorder: Optional['MidiRecorder'] = None
_start_time: float = 0.0
_previous_chord: Optional[str] = None
_stop_requested = threading.Event()


def _ensure_midi_available() -> None:
    """Check if MIDI is available (either real or softsynth)."""
    if not _HAS_MIDO and not _HAS_SYNTH:
        click.echo(
            "Error: No audio/MIDI libraries available. Install:\n"
            "  pip install python-rtmidi mido\n"
            "  OR pip install sounddevice numpy (for softsynth)"
        )
        sys.exit(1)


def _on_stop() -> None:
    """Cleanup on stop signal."""
    global _player, _listener, _dashboard, _synth, _analytics, _recorder
    
    _stop_requested.set()
    
    # Stop recorder and save session
    if _recorder:
        session = _recorder.stop_recording()
        if session:
            filepath = _recorder.export_to_midi(session)
            click.echo(f"\n💾 Session saved to: {filepath}")
    
    # End analytics session
    if _analytics:
        stats, achievements, levels = _analytics.end_session()
        if stats:
            click.echo(f"\n📊 Session stats: {stats.total_keystrokes} keystrokes, {stats.max_wpm:.1f} max WPM")
        if achievements:
            for ach in achievements:
                click.echo(f"🏆 Achievement unlocked: {ach.icon} {ach.name}")
        if levels > 0:
            level_info = _analytics.get_current_level_info()
            click.echo(f"⭐ Level up! You are now level {level_info['level']}")
    
    # Stop dashboard
    if _dashboard:
        _dashboard.stop()
    
    # Stop synthesizer
    if _synth:
        _synth.all_notes_off()
        _synth.stop()
    
    # Stop MIDI player
    if _player:
        _player.stop()
        _player = None
    
    # Stop key listener
    if _listener:
        _listener.stop()
        _listener = None


def _find_or_create_virtual_port() -> str:
    """Find or create a virtual MIDI port."""
    import mido

    port_name = "ShredCLI"
    output_names = mido.get_output_names()
    
    for n in output_names:
        if port_name.lower() in n.lower():
            return n
    
    try:
        out = mido.open_output(port_name, virtual=True)
        out.close()
        return port_name
    except Exception:
        pass
    
    for n in output_names:
        if "iac" in n.lower() or "bus" in n.lower():
            return n
    
    return port_name


def _map_wpm_to_bpm(wpm: float) -> float:
    """Map WPM to BPM with 4-tier curve."""
    if wpm <= 0:
        return 40.0
    if wpm <= 20:
        t = wpm / 20.0
        return 40.0 + t * (80.0 - 40.0)
    if wpm <= 60:
        t = (wpm - 20.0) / 40.0
        return 80.0 + t * (120.0 - 80.0)
    if wpm <= 100:
        t = (wpm - 60.0) / 40.0
        return 120.0 + t * (160.0 - 120.0)
    t = min((wpm - 100.0) / 50.0, 1.0)
    return 160.0 + t * (200.0 - 160.0)


def _bpm_update_loop() -> None:
    """Background thread that updates BPM and all systems."""
    global _player, _dashboard, _analytics, _recorder, _previous_chord

    while not _stop_requested.is_set():
        if _wpm_calc and _wpm_smoother and _auto_slow:
            wpm = _wpm_calc.get_wpm()
            target_bpm = _map_wpm_to_bpm(wpm)
            smoothed = _wpm_smoother.update(target_bpm)
            final_bpm = _auto_slow.tick(smoothed)

            if _player:
                _player.set_bpm(final_bpm)
                chord, pattern = _player.current_chord_and_pattern()
            else:
                chord, pattern = "Am", "A"

            if _previous_chord is not None and chord != _previous_chord and _analytics:
                _analytics.record_chord_progression()
            _previous_chord = chord

            if _dashboard:
                typing = _wpm_calc.seconds_since_last_key() < 1.0
                dash_update: dict = {
                    "bpm": final_bpm,
                    "wpm": wpm,
                    "chord": chord,
                    "pattern": pattern,
                    "uptime_seconds": _uptime_seconds(),
                    "is_typing": typing,
                }
                if _analytics:
                    session = _analytics.get_current_stats()
                    if session:
                        dash_update["total_keystrokes"] = session.total_keystrokes
                level_info = _analytics.get_current_level_info() if _analytics else {}
                dash_update["level"] = level_info.get("level", 1)
                dash_update["xp"] = level_info.get("xp", 0)
                _dashboard.update(**dash_update)

            if _analytics:
                _analytics.record_bpm(final_bpm, pattern)

            if _recorder:
                _recorder.record_bpm_change(final_bpm)
            
            # Write status file
            write_status({
                "pid": os.getpid(),
                "running": True,
                "bpm": round(final_bpm, 1),
                "wpm": round(wpm, 1),
                "chord": chord,
                "pattern": pattern,
                "uptime_seconds": _uptime_seconds(),
            })
            
        time.sleep(0.5)


def _uptime_seconds() -> float:
    """Get current uptime."""
    return time.time() - _start_time


def _format_uptime(seconds: float) -> str:
    """Format uptime for display."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def _note_on_callback(channel: int, note: int, velocity: int) -> None:
    """Callback for note on events - sends to softsynth."""
    global _synth, _recorder
    
    if _synth:
        _synth.note_on(channel, note, velocity)
    
    if _recorder:
        _recorder.record_event("note_on", channel, note, velocity)


def _note_off_callback(channel: int, note: int) -> None:
    """Callback for note off events."""
    global _synth, _recorder
    
    if _synth:
        _synth.note_off(channel, note)
    
    if _recorder:
        _recorder.record_event("note_off", channel, note, 0)


def _run_main(use_dashboard: bool = False, use_synth: bool = False,
              theme: str = "classical_guitar", record: bool = False) -> None:
    """Main worker that runs inside the daemon."""
    global _wpm_calc, _wpm_smoother, _auto_slow, _player, _listener
    global _start_time, _dashboard, _synth, _analytics, _recorder, _previous_chord

    _ensure_midi_available()
    _start_time = time.time()
    _previous_chord = None
    ensure_dirs()
    
    # Initialize status file
    write_status({
        "running": True, 
        "pid": os.getpid(),
        "features": {
            "dashboard": use_dashboard and _HAS_DASHBOARD,
            "synthesizer": use_synth and _HAS_SYNTH,
            "analytics": _HAS_ANALYTICS,
            "recorder": record and _HAS_RECORDER,
        }
    })
    
    # Initialize analytics
    if _HAS_ANALYTICS:
        _analytics = get_analytics()
        _analytics.start_session()
    
    # Initialize MIDI recorder
    if record and _HAS_RECORDER:
        _recorder = get_recorder()
        _recorder.start_recording(metadata={
            "theme": theme,
            "start_time": _start_time,
        })
    
    # Initialize core components
    _wpm_calc = WpmCalculator(window_size=10)
    _wpm_smoother = WpmSmoother(initial_bpm=40.0)
    _auto_slow = AutoSlowdown(
        wpm_calc=_wpm_calc,
        smoother=_wpm_smoother,
        idle_threshold=3.0,
        slowdown_duration=2.0,
        min_bpm=40.0,
    )
    
    if use_synth and _HAS_SYNTH:
        click.echo("🎹 Using built-in synthesizer (no external MIDI needed!)")
        _synth = create_synthesizer(theme)
        if _synth:
            _synth.start()

    synth_callbacks = (
        (_note_on_callback, _note_off_callback) if use_synth and _synth else (None, None)
    )

    try:
        if use_synth:
            _player = MidiPlayerThread(
                port_name="ShredCLI",
                use_midi_output=False,
                on_note_on=synth_callbacks[0],
                on_note_off=synth_callbacks[1],
            )
            _player.start()
        else:
            port_to_open = _find_or_create_virtual_port()
            on_on, on_off = synth_callbacks
            _player = MidiPlayerThread(
                port_name="ShredCLI",
                open_port_name=port_to_open,
                use_midi_output=True,
                on_note_on=on_on,
                on_note_off=on_off,
            )
            _player.start()
    except RuntimeError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    
    # Initialize dashboard
    if use_dashboard and _HAS_DASHBOARD:
        _dashboard = create_simple_dashboard()
        if _analytics:
            level_info = _analytics.get_current_level_info()
            _dashboard.update(
                level=level_info.get('level', 1),
                xp=level_info.get('xp', 0),
            )
        dashboard_thread = threading.Thread(target=_dashboard.start)
        dashboard_thread.daemon = True
        dashboard_thread.start()
    
    # Key listener
    def on_key() -> None:
        if _wpm_calc:
            _wpm_calc.add_keystroke()
            if _analytics:
                _analytics.record_keystroke(_wpm_calc.get_wpm())
    
    _listener = KeyListener(on_keystroke=on_key)
    _listener.start()
    
    # BPM updater
    updater = threading.Thread(target=_bpm_update_loop, daemon=True)
    updater.start()
    
    # Block until stop requested
    _stop_requested.wait()
    
    # Cleanup
    _on_stop()


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit.')
@click.pass_context
def cli(ctx, version):
    """Shred-CLI: type fast, shred harder. 🎸⌨️"""
    if version:
        click.echo("Shred-CLI v0.2.1")
        sys.exit(0)
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--no-daemon", is_flag=True, help="Run in foreground (no daemonize).")
@click.option("--dashboard", is_flag=True, help="Show real-time TUI dashboard.")
@click.option("--synth", is_flag=True, help="Use built-in synthesizer (no external MIDI).")
@click.option("--theme", default="classical_guitar", 
              type=click.Choice(["classical_guitar", "piano", "synthwave", "8bit", "pad", "pluck"]),
              help="Sound theme (when using synthesizer).")
@click.option("--record", is_flag=True, help="Record session to MIDI file.")
def start(no_daemon, dashboard, synth, theme, record):
    """
    Start the Shred-CLI daemon.
    
    Examples:
        shred start                    # Basic mode
        shred start --dashboard        # With live dashboard
        shred start --synth            # Built-in audio, no MIDI setup needed
        shred start --synth --theme 8bit --dashboard  # Retro gaming style!
        shred start --record           # Save your session
    """
    status = get_status()
    if status["running"]:
        click.echo(f"Shred-CLI is already running (PID {status['pid']}).")
        sys.exit(0)
    
    # Feature availability warnings
    if dashboard and not _HAS_DASHBOARD:
        click.echo("⚠️  Dashboard requires 'rich'. Install: pip install rich")
        dashboard = False
    
    if synth and not _HAS_SYNTH:
        click.echo("⚠️  Synthesizer requires 'sounddevice'. Install: pip install sounddevice numpy")
        synth = False
    
    if record and not _HAS_RECORDER:
        click.echo("⚠️  Recording requires 'mido'. Install: pip install mido")
        record = False
    
    # Build startup message
    features = []
    if dashboard:
        features.append("📊 dashboard")
    if synth:
        features.append(f"🎹 synthesizer ({theme})")
    if record:
        features.append("⏺️  recording")
    
    feature_msg = f" with {', '.join(features)}" if features else ""
    
    def run_with_features():
        _run_main(
            use_dashboard=dashboard,
            use_synth=synth,
            theme=theme,
            record=record,
        )
    
    runner = DaemonRunner(main_func=run_with_features, on_sigterm=_on_stop)
    
    if no_daemon:
        click.echo(f"🎸 Shred-CLI starting in foreground{feature_msg}")
        click.echo("Press Ctrl+C to stop. Start typing to shred!")
        runner.start(daemonize=False)
    else:
        pid = runner.start(daemonize=True)
        if pid:
            click.echo(f"🎸 Shred-CLI started (PID {pid}){feature_msg}")
            click.echo("Start typing to shred! Use 'shred status' to check stats.")
        else:
            click.echo(f"🎸 Shred-CLI started{feature_msg}. Start typing to shred!")


@cli.command()
def stop():
    """Stop the Shred-CLI daemon."""
    if stop_daemon():
        click.echo("🛑 Shred-CLI stopped. Great session!")
    else:
        click.echo("Shred-CLI is not running.")


@cli.command()
def status():
    """Show current Shred-CLI status."""
    s = get_status()
    if not s["running"]:
        click.echo("Status: stopped")
        return
    
    pid = s.get("pid")
    click.echo(f"🎸 Status: running (PID {pid})")
    
    details = read_status()
    if details:
        click.echo(f"   BPM: {details.get('bpm', 'N/A')}")
        click.echo(f"   WPM: {details.get('wpm', 'N/A')}")
        click.echo(f"   Chord: {details.get('chord', 'N/A')}")
        click.echo(f"   Pattern: {details.get('pattern', 'N/A')}")
        
        uptime = details.get('uptime_seconds')
        if uptime is not None:
            click.echo(f"   Uptime: {_format_uptime(uptime)}")
        
        # Show features
        features = details.get('features', {})
        if any(features.values()):
            click.echo("   Features:")
            for name, enabled in features.items():
                if enabled:
                    click.echo(f"     ✓ {name}")
    else:
        click.echo("   (Detailed metrics not yet available)")


@cli.command()
def stats():
    """Show detailed typing statistics and achievements."""
    if not _HAS_ANALYTICS:
        click.echo("Analytics module not available. Install dependencies.")
        return
    
    analytics = get_analytics()
    summary = analytics.get_user_summary()
    
    click.echo("\n📊 Your Shred-CLI Statistics")
    click.echo("=" * 40)
    
    user = summary['user']
    click.echo(f"\n🎯 Level {user['current_level']} ({user['current_xp']}/{user['xp_to_next_level']} XP)")
    click.echo(f"📈 Total Sessions: {user['total_sessions']}")
    click.echo(f"⌨️  Total Keystrokes: {user['total_keystrokes_all_time']:,}")
    click.echo(f"⏱️  Total Typing Time: {user['total_typing_time_hours']:.1f} hours")
    click.echo(f"🏆 Highest WPM: {user['highest_wpm_ever']:.1f}")
    click.echo(f"🎵 Chords Played: {user['total_chords_played']}")
    
    heatmap = summary['heatmap']
    peak_hour, peak_count = heatmap['peak_hour']
    click.echo(f"\n🔥 Peak Hour: {peak_hour}:00 ({peak_count} keystrokes)")
    click.echo(f"📉 Average WPM: {heatmap['avg_wpm']:.1f}")
    
    # Achievements
    click.echo(f"\n🏆 Achievements ({len(user['achievements_unlocked'])} unlocked)")
    for ach in summary['achievements']:
        status = "✓" if ach['unlocked'] else "○"
        click.echo(f"   {status} {ach['icon']} {ach['name']}: {ach['description']}")


@cli.command()
@click.option("--list", "list_themes", is_flag=True, help="List available themes.")
@click.option("--preview", help="Preview a theme (specify theme name).")
def themes(list_themes, preview):
    """Manage sound themes for the synthesizer."""
    if not _HAS_SYNTH:
        click.echo("Synthesizer not available. Install: pip install sounddevice numpy")
        return
    
    if preview:
        if preview not in THEMES:
            click.echo(f"Unknown theme: {preview}")
            return
        
        click.echo(f"🎵 Previewing {preview} theme...")
        synth = create_synthesizer(preview)
        if synth:
            synth.start()
            
            # Play a short C major arpeggio
            notes = [(0, 60, 100), (1, 64, 100), (2, 67, 100), (0, 72, 100)]
            for ch, note, vel in notes:
                synth.note_on(ch, note, vel, 400)
                time.sleep(0.5)
            
            time.sleep(1)
            synth.stop()
            click.echo("Preview complete!")
        return

    # Default: list themes (also when --list is passed)
    click.echo("\n🎹 Available Sound Themes:")
    click.echo("=" * 40)
    for name, theme in THEMES.items():
        click.echo(f"\n  {name}")
        click.echo(f"    Waveform: {theme.waveform.value}")
        click.echo(f"    Character: {theme.name}")
    click.echo("\nUsage: shred start --synth --theme <name>")


@cli.command()
@click.option("--list", "list_recordings", is_flag=True, help="List recorded sessions.")
@click.option("--export", type=int, help="Export session by index to MIDI file.")
@click.option("--play", type=int, help="Play back a recorded session.")
@click.option("--delete", type=int, help="Delete a recorded session.")
def export(list_recordings, export, play, delete):
    """Manage recorded MIDI sessions."""
    if not _HAS_RECORDER:
        click.echo("Recorder not available. Install: pip install mido")
        return
    
    recorder = get_recorder()
    
    if list_recordings:
        sessions = recorder.get_session_summary()
        if not sessions:
            click.echo("No recordings found.")
            return
        
        click.echo("\n📼 Recorded Sessions:")
        click.echo("=" * 60)
        for i, s in enumerate(sessions):
            click.echo(f"\n[{i}] {s['date'][:19]}")
            click.echo(f"    Duration: {s['duration_seconds']:.1f}s")
            click.echo(f"    Notes: {s['note_count']} events: {s['event_count']}")
    
    elif export is not None:
        sessions = recorder.get_sessions()
        if export < 0 or export >= len(sessions):
            click.echo(f"Invalid session index: {export}")
            return
        
        filepath = recorder.export_to_midi(sessions[export])
        click.echo(f"✓ Exported to: {filepath}")
    
    elif delete is not None:
        if recorder.delete_session(delete):
            click.echo(f"✓ Deleted session {delete}")
        else:
            click.echo(f"Invalid session index: {delete}")
    
    elif play is not None:
        click.echo("Playback not yet implemented in CLI.")
    
    else:
        click.echo("Use --list to see recordings or --export <index> to save as MIDI.")


@cli.command()
@click.option("--duration", default=30, help="Demo duration in seconds.")
@click.option("--theme", default="synthwave", help="Sound theme for demo.")
@click.option("--synth/--no-synth", default=True, help="Use built-in synthesizer (default: on).")
@click.option("--dashboard/--no-dashboard", default=False, help="Show live TUI dashboard.")
def demo(duration, theme, synth, dashboard):
    """Run an automated demo mode (types for you!)."""
    if synth and not _HAS_SYNTH:
        click.echo("Synthesizer not available. Install: pip install 'shred-cli[all]'")
        sys.exit(1)

    features = []
    if synth:
        features.append(f"synth ({theme})")
    if dashboard:
        features.append("dashboard")
    feat = f" ({', '.join(features)})" if features else ""

    click.echo(f"🎸 Starting demo mode for {duration} seconds{feat}...")
    click.echo("Sit back and enjoy the show!")

    def run_demo():
        _run_main(use_dashboard=dashboard, use_synth=synth, theme=theme)
    
    # Start in background thread
    demo_thread = threading.Thread(target=run_demo)
    demo_thread.daemon = True
    
    # Simulate keystrokes in another thread
    def auto_type():
        time.sleep(2)  # Wait for startup
        patterns = [
            # Slow typing
            ([20] * 10, 0.5),
            # Medium typing  
            ([50] * 20, 0.3),
            # Fast typing
            ([100] * 30, 0.15),
            # Shredding!
            ([150] * 40, 0.1),
            # Slow down
            ([80] * 15, 0.3),
            ([40] * 10, 0.5),
        ]
        
        for wpm_list, delay in patterns:
            for wpm in wpm_list:
                if _wpm_calc:
                    _wpm_calc.add_keystroke()
                time.sleep(delay)
    
    demo_thread.start()
    time.sleep(2)  # Let it start
    
    typer = threading.Thread(target=auto_type)
    typer.start()
    typer.join(duration)
    
    _stop_requested.set()
    demo_thread.join(timeout=5.0)
    _on_stop()
    click.echo("\n✨ Demo complete!")


def main() -> None:
    """Console entry point for setuptools."""
    cli()


# Compatibility for direct module run
if __name__ == "__main__":
    main()
