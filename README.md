# Shred-CLI

**Type fast. Shred harder.** A background CLI daemon that turns your typing speed into live classical-guitar arpeggios.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Chessing234/shred-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Chessing234/shred-cli/actions/workflows/ci.yml)

```
     ╔═══════════════════════════════════════════════════════════╗
     ║     🎸  SHRED-CLI  —  Type → WPM → BPM → Arpeggios  🎸    ║
     ╚═══════════════════════════════════════════════════════════╝

      ⌨️  keystrokes          ♪  tempo follows you
      🎸  Am → Dm → E7 → F    📈  stats, XP, achievements
```

## Install

**macOS (recommended):** install PortAudio first, then the package.

```bash
brew install portaudio
pip install "shred-cli[all]"
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt-get install -y libasound2-dev portaudio19-dev
pip install "shred-cli[all]"
```

**Minimal (external MIDI only, no built-in audio):**

```bash
pip install shred-cli
```

## Quickstart

```bash
# 1. Built-in synth — no MIDI setup required
shred start --no-daemon --synth --theme synthwave

# 2. See your lifetime stats
shred stats

# 3. Run a 30-second auto-demo
shred demo --synth --theme synthwave --duration 30
```

Press `Ctrl+C` to stop when running in the foreground.

## Features

- **Global keyboard listener** — tracks WPM across all apps (never blocks your typing)
- **WPM → BPM mapping** — four tempo zones from Adagio to Presto
- **Grade 8 guitar patterns** — p-i-m-a, Alzapúa, tremolo, rasgueado
- **Chord progression** — Am → Dm → E7 → F → C → G
- **Built-in synthesizer** — six themes, no DAW required
- **Rich TUI dashboard** — live BPM, WPM, chords, XP
- **Analytics & achievements** — persisted in `~/.shredcli/`
- **MIDI recording** — export sessions as `.mid`
- **Cross-platform daemon** — macOS, Linux, Windows

### Sound themes

| Theme | Style |
|-------|--------|
| `classical_guitar` | Nylon-string fingerstyle |
| `piano` | Grand piano |
| `synthwave` | Retro saw synth |
| `8bit` | Chiptune square waves |
| `pad` | Ambient sine pad |
| `pluck` | Harp-like plucks |

List themes: `shred themes`

## CLI reference

| Command | Description |
|---------|-------------|
| `shred start` | Start the daemon |
| `shred stop` | Stop the daemon |
| `shred status` | Running state, BPM, WPM, chord |
| `shred stats` | Lifetime stats and achievements |
| `shred themes` | List synthesizer themes |
| `shred themes --preview NAME` | Preview a theme |
| `shred export --list` | List recorded sessions |
| `shred export --export N` | Export session `N` to `.mid` |
| `shred demo` | Automated typing demo |

### `shred start` flags

| Flag | Description |
|------|-------------|
| `--no-daemon` | Foreground mode (debugging) |
| `--synth` | Built-in audio engine |
| `--theme NAME` | Synth theme (see table above) |
| `--dashboard` | Rich live TUI |
| `--record` | Record session for MIDI export |

### `shred demo` flags

| Flag | Default | Description |
|------|---------|-------------|
| `--duration SEC` | `30` | Demo length |
| `--theme NAME` | `synthwave` | Synth theme |
| `--synth / --no-synth` | on | Built-in audio |
| `--dashboard / --no-dashboard` | off | Live TUI |

## Configuration

Optional config: `~/.shredcli/config.json` (see `examples/config.json`).

Runtime data: `~/.shredcli/` (PID, logs, stats, recordings).

## Known limitations

1. **macOS Accessibility** — `pynput` needs **System Settings → Privacy & Security → Accessibility** for the terminal or Python. Without it, WPM stays at zero and tempo does not rise.
2. **Audio device** — built-in synth needs a working output device and PortAudio (`brew install portaudio` on macOS).
3. **MIDI mode** — external MIDI requires a virtual port (macOS: enable **IAC Driver** in Audio MIDI Setup).
4. **Daemon + dashboard** — the Rich dashboard is intended for foreground (`--no-daemon`); background daemon mode writes status to `~/.shredcli/status.json` instead.

## Development

```bash
git clone https://github.com/Chessing234/shred-cli.git
cd shred-cli
pip install -e ".[all,dev]"
pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © [Taksh Kothari](https://github.com/Chessing234)
