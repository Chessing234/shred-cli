# Shred-CLI

Type fast, shred harder. Shred-CLI runs in the background, watches how fast you type, and plays classical-guitar arpeggios that speed up with your WPM. Faster typing → higher BPM → louder shredding.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Chessing234/shred-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Chessing234/shred-cli/actions/workflows/ci.yml)

## Try it (macOS)

```bash
brew install portaudio
pip install "shred-cli[all]"

shred start --no-daemon --synth --theme synthwave
```

Type in any app. `Ctrl+C` to quit.

No PyPI yet? Use the [latest release wheel](https://github.com/Chessing234/shred-cli/releases/latest) instead of `pip install shred-cli`.

**Linux:** `sudo apt install libasound2-dev portaudio19-dev`, then the same `pip` line.

## What it does

- Listens to keystrokes globally (doesn't block your typing)
- Maps typing speed to tempo (slow crawl → full presto)
- Cycles chords (Am → Dm → E7 → F → C → G) with real arpeggio patterns
- Optional built-in synth (`--synth`) — no MIDI rig required
- Optional dashboard (`--dashboard`), stats/XP (`shred stats`), record to `.mid` (`--record`)

Themes: `classical_guitar`, `piano`, `synthwave`, `8bit`, `pad`, `pluck` — run `shred themes` to list them.

## Commands

```
shred start [--synth] [--theme NAME] [--dashboard] [--record] [--no-daemon]
shred stop
shred status
shred stats
shred themes [--preview NAME]
shred export --list
shred export --export 0
shred export --play 0
shred demo --synth --duration 30
```

`shred demo` fakes keystrokes for you — handy for showing someone how it works.

## Heads up (macOS especially)

- **Accessibility:** give your terminal Accessibility permission or WPM stays at 0. System Settings → Privacy & Security → Accessibility.
- **Sound:** synth mode needs PortAudio (`brew install portaudio`) and speakers/headphones.
- **MIDI mode** (no `--synth`): you need a virtual MIDI port — on Mac, turn on the IAC Driver in Audio MIDI Setup.

Config lives in `~/.shredcli/` if you want to tweak things (`examples/config.json`).

## Hack on it

```bash
git clone https://github.com/Chessing234/shred-cli.git
cd shred-cli
pip install -e ".[all,dev]"
pytest
```

MIT — Taksh Kothari
