# Contributing to Shred-CLI

Thank you for your interest in contributing to Shred-CLI! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/Chessing234/shred-cli.git
   cd shred-cli
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e .
   pip install pytest black flake8 mypy
   ```

4. **Verify the installation:**
   ```bash
   python3 -m shredcli.cli --help
   ```

## Code Structure

```
shredcli/
  __init__.py      # Package metadata
  cli.py           # CLI entry point (Click commands)
  config.py        # Configuration management
  daemon.py        # Cross-platform daemonization
  listener.py      # Keyboard listener + WPM calculation
  player.py        # MIDI thread and arpeggio engine
  theory.py        # Chord voicings and patterns
tests/
  test_*.py        # Unit tests for each module
```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes:**
   - Follow PEP 8 style guide
   - Add type hints where appropriate
   - Update tests as needed

3. **Run tests:**
   ```bash
   make test
   # Or directly:
   pytest tests/ -v
   ```

4. **Check code quality:**
   ```bash
   make lint
   # Or manually:
   black shredcli/
   flake8 shredcli/ --max-line-length=120
   mypy shredcli/ --ignore-missing-imports
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature X"
   ```

6. **Push and create PR:**
   ```bash
   git push origin feature/my-new-feature
   ```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Build/tooling changes

## Testing

### Writing Tests

Tests are in the `tests/` directory. Each module has a corresponding test file:

```python
# tests/test_theory.py
import pytest
from shredcli.theory import PROGRESSION

class TestVoicings:
    def test_progression_has_6_chords(self):
        assert len(PROGRESSION) == 6
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_theory.py -v

# Run with coverage
pytest --cov=shredcli --cov-report=html
```

## Code Style

- **Line length:** 120 characters maximum
- **Quotes:** Use double quotes for strings
- **Imports:** Group imports: stdlib, third-party, local
- **Type hints:** Use where beneficial for clarity

Example:

```python
from __future__ import annotations

import time
from typing import Optional

import click

from shredcli.theory import PROGRESSION


def process_input(value: str, timeout: Optional[float] = None) -> int:
    """Process the input string and return count."""
    if timeout:
        time.sleep(timeout)
    return len(value)
```

## Adding New Features

### Adding a New Arpeggio Pattern

1. Define the pattern in `theory.py`:

```python
def pattern_f(v: Voicing) -> List[ArpStep]:
    """Your new pattern description."""
    b, m, t = v.bass, v.mid, v.treble
    return [
        _step([(CH_BASS, b[0])]),
        _step([(CH_TREBLE, t[0]), (CH_TREBLE, t[1])]),  # Double stop
        _step([(CH_MID, m[0])]),
    ]
```

2. Add to `PATTERN_FUNCTIONS` and `PATTERN_LABELS`:

```python
PATTERN_FUNCTIONS: Tuple[PatternFn, ...] = (
    pattern_a,
    pattern_b,
    pattern_c,
    pattern_d,
    pattern_e,
    pattern_f,  # Add new pattern
)

PATTERN_LABELS = ("A", "B", "C", "D", "E", "F")
```

3. Add tests in `tests/test_theory.py`

### Adding a New CLI Command

1. Add command in `cli.py`:

```python
@cli.command()
@click.option("--option", help="Description")
def mycommand(option):
    """Command description for help text."""
    click.echo(f"Option value: {option}")
```

2. Add tests in `tests/`

## Documentation

- Update README.md for user-facing changes
- Update examples/ for new configuration options
- Add docstrings to public functions

## MIDI Testing

Since Shred-CLI outputs MIDI, testing audio requires:

1. Virtual MIDI driver or DAW
2. Synthesizer (hardware or software)

For automated testing, we mock MIDI output.

## Platform-Specific Notes

### macOS
- Requires Accessibility permissions for keyboard input
- IAC Driver for MIDI routing

### Linux
- Requires ALSA libraries
- May need input group membership

### Windows
- No special permissions needed
- LoopBe1 or similar for virtual MIDI

## Release Process

1. Update version in `__init__.py`
2. Update CHANGELOG
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
