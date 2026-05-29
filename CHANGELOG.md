# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-05-28

Production release: bug fixes, synth routing, persistence, CI/CD, and public packaging.

### Changed

- Shorter, clearer README
- `shred export --play` replays recordings through the built-in synth
- Version string comes from package metadata; docs URLs aligned with GitHub repo

### Fixed

- Synthesizer: `_HAS_SOUNDDEVICE` NameError when sounddevice is installed
- Synth mode: route arpeggio events to built-in audio (was silent)
- Synth-only mode no longer requires an external MIDI port
- Analytics: stop inflating keystroke counts from the BPM poll loop
- Analytics: persist level, XP, and achievements across restarts
- Recorder: export valid `.mid` files with tempo meta and absolute timing
- `shred themes` lists themes by default; `shred demo` supports `--synth` flag

### Added

- Tests for synthesizer, recorder, analytics, player callbacks
- GitHub Actions CI (Python 3.9–3.12) and release workflow
- Issue templates, production README, PyPI packaging metadata

## [0.2.0] - 2026-05-27

Hackathon edition: dashboard, synthesizer, analytics, gamification, recording, demo mode.

### Added

- Rich TUI dashboard (`--dashboard`)
- Built-in software synthesizer with six themes (`--synth`)
- Analytics, XP, and ten achievements (`shred stats`)
- MIDI session recording and export (`--record`, `shred export`)
- Demo mode (`shred demo`)
- CLI commands: `stats`, `themes`, `export`, `demo`

## [0.1.0] - 2026-05-27

Initial release.

### Added

- Global keyboard listener and WPM calculation
- WPM → BPM mapping with exponential smoothing
- Grade 8 classical guitar arpeggios and chord progression
- Cross-platform daemon (`start` / `stop` / `status`)
- Configuration file support and core test suite

[Unreleased]: https://github.com/Chessing234/shred-cli/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/Chessing234/shred-cli/releases/tag/v0.2.1
[0.2.0]: https://github.com/Chessing234/shred-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/Chessing234/shred-cli/releases/tag/v0.1.0
