# v0.2.1 — Shred-CLI Production Release

**Type fast. Shred harder.** Shred-CLI is a background daemon that listens to your typing speed and plays Grade 8 classical-guitar arpeggios in real time — faster typing, faster tempo.

## Install

```bash
brew install portaudio   # macOS only
pip install "shred-cli[all]"
```

## Try it in three commands

```bash
shred start --no-daemon --synth --theme synthwave
shred stats
shred demo --synth --theme 8bit --duration 30
```

## Highlights

- Built-in synthesizer with six themes (no MIDI setup required)
- WPM → BPM mapping with smooth tempo transitions
- Rich optional dashboard, XP, and achievements
- Export typing sessions as standard MIDI files
- 102 automated tests, CI on Python 3.9–3.12

## Known limitations

- **macOS:** grant Accessibility to your terminal for global key listening
- **Audio:** requires a working output device and PortAudio on macOS
- **MIDI mode:** needs a virtual MIDI port (IAC Driver on macOS)

## Links

- Repository: https://github.com/takshkothari/shred-cli
- Changelog: https://github.com/takshkothari/shred-cli/blob/main/CHANGELOG.md
