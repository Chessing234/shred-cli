# 🎸 Shred-CLI ⌨️

> **Type fast, shred harder.** A MIDI-generating typing companion that transforms your keystrokes into Grade 8 classical guitar arpeggios in real-time.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

```
     ╔═══════════════════════════════════════════════════════════╗
     ║                                                           ║
     ║     🎸  SHRED-CLI  v0.2.0  🎸                             ║
     ║                                                           ║
     ║     Type fast → Generate MIDI → Make Music               ║
     ║                                                           ║
     ╚═══════════════════════════════════════════════════════════╝
```

## ✨ Features

### 🎵 Core Features
- **Global key listener** — Tracks keystrokes across all applications (non-blocking, never intercepts your typing)
- **Real-time WPM → BPM mapping** — Your typing speed becomes the music tempo
- **Grade 8 classical guitar patterns** — Authentic p-i-m-a, Alzapúa, Tremolo, and Rasgueado arpeggios
- **Authentic chord progression** — Cycles through Am → Dm → E7 → F → C → G
- **Multi-voiced MIDI output** — Bass, mid, and treble voices on separate channels

### 🎮 Hackathon Edition Extras

#### 🖥️ Beautiful TUI Dashboard
```bash
shred start --dashboard
```
Real-time visualization with:
- Live BPM gauge with tempo zones (Adagio → Presto!)
- WPM speedometer with session high tracking
- Current chord and arpeggio pattern display
- Level and XP progress bar
- Achievement unlock notifications
- Chord progression history

#### 🎹 Built-in Synthesizer (No MIDI Setup Required!)
```bash
shred start --synth --theme synthwave
```
6 amazing sound themes:
- **classical_guitar** — Authentic nylon-string tones
- **piano** — Grand piano with reverb
- **synthwave** — 80s retro synth sounds
- **8bit** — Retro gaming chiptune style
- **pad** — Ambient atmospheric pads
- **pluck** — Harp-like plucked tones

#### 📊 Analytics & Stats
```bash
shred stats
```
Track everything:
- Total keystrokes, typing time, sessions
- Highest WPM ever achieved
- Time spent in each tempo zone
- Peak typing hour heatmap
- Average WPM over time

#### 🏆 Gamification
- **Level system** — Gain XP from typing, unlock levels
- **10 Achievements** to unlock:
  - 👶 First Steps — Type your first keystroke
  - ⚡ Speed Demon — Reach 100 WPM
  - 🔥 Shredder — 30 seconds at 160+ BPM
  - 🎼 Maestro — Complete 10 chord progressions
  - 👑 Master Shredder — Reach level 10
  - And more!

#### ⏺️ Recording & Export
```bash
shred start --record           # Record your session
shred export --list            # List recordings
shred export --export 0        # Save as MIDI file
```
Export your typing sessions as standard MIDI files for use in your DAW!

#### 🎬 Demo Mode
```bash
shred demo --duration 60 --theme 8bit
```
Automated demo that types for you — perfect for presentations!

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/your-username/shred-cli.git
cd shred-cli

# Basic install (requires external MIDI setup)
pip install -e .

# OR full install with all features (recommended!)
pip install -e ".[all]"

# OR with specific features
pip install -e ".[dashboard,synth]"
```

### One-Liner Demo

```bash
# No MIDI setup needed! Built-in synth + dashboard:
shred start --synth --dashboard --theme synthwave
```

## 📖 Usage

### Basic Usage (requires MIDI setup)
```bash
shred start              # Start in background
shred stop               # Stop daemon
shred status             # Check current stats
```

### With Dashboard (Beautiful!)
```bash
shred start --dashboard              # Real-time TUI
shred start --dashboard --synth      # + built-in audio
```

### Built-in Synthesizer (No MIDI Setup!)
```bash
# Choose your sound
shred start --synth --theme classical_guitar
shred start --synth --theme piano
shred start --synth --theme synthwave
shred start --synth --theme 8bit

# List themes
shred themes --list

# Preview a theme
shred themes --preview synthwave
```

### Record Your Sessions
```bash
shred start --record                    # Record to memory
shred export --list                     # See recordings
shred export --export 0                 # Save as .mid file
```

### View Statistics
```bash
shred stats              # All-time stats
shred stats --session    # Current session only
```

### Demo Mode (Auto-typing)
```bash
shred demo                           # 30-second demo
shred demo --duration 60            # 60-second demo
shred demo --theme 8bit             # Retro style demo
```

## 🖥️ Dashboard Preview

```
╔═══════════════════════════════════════════════════════════╗
║           🎸 SHRED-CLI  🎸 Type Fast, Shred Harder!        ║
╚═══════════════════════════════════════════════════════════╝
┌──────────────┬──────────────┬──────────────┐
│  ♪ Tempo ♪   │   ⌨️ WPM     │   🎸 Guitar  │
│  142.5 BPM   │   85.3      │   Chord: Am  │
│ [████████░░] │   Session   │   Pattern: A │
│    Allegro   │   High: 120 │   p-i-m-a    │
└──────────────┴──────────────┴──────────────┘
┌──────────────┬──────────────┐
│ 📊 Session   │ ⭐ Progress  │
│ Keystrokes:  │ Level 3      │
│ 1,234        │ XP: 450/1000 │
│ Uptime: 5m   │ [████░░░░░░] │
└──────────────┴──────────────┘
┌──────────────────────────────────┐
│ 🎵 Am → Dm → E7 → F → C → G    │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│ 🏆 Achievements                  │
│ ⚡ Speed Demon                  │
│ 🔥 Shredder                     │
└──────────────────────────────────┘
[Ctrl+C] Stop | Type faster → Higher BPM → 🔥
```

## 🎹 Tempo Zones

Your typing speed creates different musical moods:

| Typing Speed | BPM Range | Musical Term | Feel |
|--------------|-----------|--------------|------|
| 0–20 WPM | 40–80 | 🐢 Adagio | Sparse, contemplative |
| 20–60 WPM | 80–120 | 🚶 Andante | Walking pace, flowing |
| 60–100 WPM | 120–160 | 🏃 Allegro | Quick, lively |
| 100+ WPM | 160–200 | 🔥 Presto | Very fast, shredding! |

## 🎸 Arpeggio Patterns

Five authentic classical guitar patterns rotate with each chord:

1. **Pattern A (p-i-m-a)** — Thumb-Index-Middle-Ring (classical)
2. **Pattern B (p-a-m-i)** — Thumb-Ring-Middle-Index (reverse)
3. **Pattern C (Alzapúa)** — Thumb pinch + treble figures (flamenco)
4. **Pattern D (Tremolo)** — Bass + rapid treble strokes
5. **Pattern E (Rasgueado)** — Full chord strum up and down

## 🛠️ Platform Setup

### macOS
```bash
# 1. Grant Accessibility permissions
#    System Preferences → Privacy & Security → Accessibility → Add Terminal

# 2. For real MIDI (optional with --synth):
#    Audio MIDI Setup → Show MIDI Studio → IAC Driver → Enable

# 3. Install
pip install -e ".[all]"
```

### Linux
```bash
# 1. Install ALSA development libraries
sudo apt-get install libasound2-dev  # Debian/Ubuntu
sudo dnf install alsa-lib-devel      # Fedora

# 2. Add user to input group
sudo usermod -a -G input $USER
# Log out and back in

# 3. Install
pip install -e ".[all]"
```

### Windows
```bash
# Just install! No special permissions needed
pip install -e ".[all]"

# For real MIDI routing, install LoopBe1 virtual MIDI driver
```

## 📁 Project Structure

```
shredcli/
  __init__.py           # Package metadata
  cli.py                # Click CLI with all commands
  config.py             # Configuration management
  daemon.py             # Cross-platform daemonization
  listener.py           # Global keyboard + WPM calculation
  player.py             # MIDI thread + scheduler
  theory.py             # Chord voicings + arpeggio patterns
  dashboard.py          # 🆕 Rich TUI visualization
  analytics.py          # 🆕 Stats tracking + achievements
  synthesizer.py        # 🆕 Built-in softsynth
  recorder.py           # 🆕 MIDI recording + export
tests/                  # Comprehensive test suite
examples/               # Configuration examples
scripts/
  setup.sh              # Automated setup script
```

## 🔧 Configuration

Create `~/.shredcli/config.json` to customize:

```json
{
  "timing": {
    "smoothing_alpha": 0.2,
    "idle_threshold_seconds": 3.0
  },
  "midi": {
    "port_name": "ShredCLI",
    "tick_ms": 10
  },
  "velocity": {
    "bass": {"min": 90, "max": 110},
    "mid": {"min": 60, "max": 80},
    "treble": {"min": 70, "max": 95}
  }
}
```

## 🧪 Testing

```bash
make install-dev    # Install dev dependencies
make test           # Run test suite
make lint           # Check code style
```

## 🐛 Troubleshooting

### No audio output
```bash
# Use built-in synth (no MIDI setup needed!)
shred start --synth --theme classical_guitar

# Check available themes
shred themes --list
```

### Dashboard not showing
```bash
# Install rich library
pip install rich

# Or reinstall with dashboard support
pip install -e ".[dashboard]"
```

### Permission denied (keyboard input)
```bash
# macOS: Grant Accessibility to Terminal in System Preferences
# Linux: Run 'sudo usermod -a -G input $USER' and log out/in
```

## 📝 Logging

```bash
# View logs
tail -f ~/.shredcli/shred.log

# View recordings
ls ~/.shredcli/recordings/

# View stats
cat ~/.shredcli/stats.json
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

```bash
make install-dev
make test
make lint
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Classical guitar patterns based on Grade 8 ABRSM repertoire
- MIDI implementation follows General MIDI specification
- Built with [pynput](https://github.com/moses-palmer/pynput), [mido](https://github.com/mido/mido), and [rich](https://github.com/Textualize/rich)

---

<p align="center">
  <strong>Type fast. Shred harder. 🎸⌨️</strong>
</p>
