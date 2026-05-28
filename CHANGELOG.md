# Changelog

All notable changes to Shred-CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-05-28

### Fixed
- Synthesizer: `_HAS_SOUNDDEVICE` NameError when sounddevice is installed
- Synth mode: route arpeggio MIDI events to built-in audio (was silent)
- Synth-only mode no longer requires an external MIDI port
- Analytics: stop inflating keystroke counts from the BPM poll loop
- Analytics: persist level, XP, and achievements across restarts
- Recorder: export valid `.mid` files with tempo meta and absolute timing

### Added
- Tests for synthesizer, recorder export, analytics persistence, player callbacks

## [0.2.0] - 2026-05-27 - Hackathon Edition

### 🎉 New Features (Hackathon Edition!)

#### 🖥️ TUI Dashboard
- Beautiful real-time terminal dashboard using Rich library
- Live BPM gauge with color-coded tempo zones
- WPM speedometer with session high tracking
- Current chord and pattern display
- Level/XP progress bar
- Achievement notifications
- Chord progression history

#### 🎹 Built-in Software Synthesizer
- No external MIDI setup required!
- 6 different sound themes:
  - Classical Guitar (authentic nylon-string emulation)
  - Piano (grand piano with reverb)
  - Synthwave (80s retro synthesizer)
  - 8-bit (retro gaming chiptune style)
  - Pad (ambient atmospheric)
  - Pluck (harp-like tones)
- Real-time waveform generation with ADSR envelopes
- Low-pass filtering and effects

#### 📊 Analytics & Statistics
- Comprehensive typing performance tracking
- Session history (last 100 sessions)
- WPM heatmaps by hour
- Total keystrokes, typing time
- Peak performance hour tracking
- Persistent storage in ~/.shredcli/

#### 🏆 Gamification System
- Level progression with XP system
- 10 unlockable achievements:
  - 👶 First Steps
  - ⚡ Speed Demon (100 WPM)
  - 🏃 Marathon Typist (5 minutes)
  - 💯 Century Club (100 keystrokes)
  - 🔥 Shredder (30s at 160+ BPM)
  - 🎼 Maestro (10 progressions)
  - 🎸 Well Rounded (all patterns)
  - 🌩️ Lightning Fingers (150 WPM)
  - 🎖️ Veteran (10 sessions)
  - 👑 Master Shredder (Level 10)

#### ⏺️ Recording & Export
- Record MIDI sessions to memory
- Export to standard MIDI files (.mid)
- Playback of recorded sessions
- Automatic session saving
- Recording library management

#### 🎬 Demo Mode
- Automated typing demonstration
- Configurable duration and theme
- Perfect for presentations and testing

#### 🔧 Enhanced CLI
- New commands: `stats`, `themes`, `export`, `demo`
- Feature flags: `--dashboard`, `--synth`, `--record`
- Theme selection: `--theme <name>`
- Better error messages and help text

### Changed
- Daemon startup logic improved for reliability
- Better platform detection and setup
- Enhanced documentation with examples
- Makefile with more helpful targets

### Fixed
- PID file handling in daemon mode
- Better cleanup on SIGTERM/SIGINT
- Proper MIDI port discovery on all platforms

## [0.1.0] - 2026-05-27

### Added
- Initial release of Shred-CLI
- Global keyboard listener using pynput
- Real-time WPM to BPM mapping with exponential smoothing
- Four-tier tempo curve (Adagio, Andante, Allegro, Presto)
- Grade 8 classical guitar arpeggios
- Cross-platform daemon support
- Configuration file support
- Comprehensive test suite

[Unreleased]: https://github.com/example/shred-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/example/shred-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/example/shred-cli/releases/tag/v0.1.0
