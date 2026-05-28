# Shred-CLI Examples

This directory contains example configurations and usage patterns for Shred-CLI.

## Configuration

Copy `config.json` to `~/.shredcli/config.json` to customize settings:

```bash
mkdir -p ~/.shredcli
cp examples/config.json ~/.shredcli/config.json
```

## Common Workflows

### Testing in Foreground Mode

Always test in foreground first to ensure MIDI is working:

```bash
shred start --no-daemon
```

Press Ctrl+C to stop.

### Running as Background Daemon

Once confirmed working:

```bash
shred start
shred status
shred stop
```

### Viewing Logs

```bash
tail -f ~/.shredcli/shred.log
```

## Platform-Specific Setups

### macOS

1. Enable IAC Driver:
   - Open Audio MIDI Setup
   - Window → Show MIDI Studio
   - Double-click "IAC Driver"
   - Check "Device is online"

2. Route to DAW:
   - Open GarageBand, Logic, or SimpleSynth
   - Create a software instrument track
   - Set input to "IAC Driver Bus 1" or "ShredCLI"

3. Grant permissions:
   - System Preferences → Privacy & Security → Accessibility
   - Add your terminal application

### Linux

1. Install ALSA development libraries:
   ```bash
   # Debian/Ubuntu
   sudo apt-get install libasound2-dev

   # Fedora
   sudo dnf install alsa-lib-devel
   ```

2. Add user to input group:
   ```bash
   sudo usermod -a -G input $USER
   # Log out and back in
   ```

3. Route to synthesizer:
   ```bash
   # Using FluidSynth
   qsynth &
   # Or connect to DAW with QJackCtl
   ```

### Windows

1. Install LoopBe1 or similar virtual MIDI driver
2. Configure your DAW to listen to the virtual port
3. No additional permissions needed

## Troubleshooting

### "No MIDI output ports available"

- macOS: Enable IAC Driver in Audio MIDI Setup
- Linux: Check `aplaymidi -l` for available ports
- Windows: Install a virtual MIDI driver like LoopBe1

### "Permission denied" for keyboard input

- macOS: Grant Accessibility permissions in System Preferences
- Linux: Add user to `input` group and log out/back in

### No sound even though daemon is running

1. Check MIDI routing to your synthesizer/DAW
2. Verify the virtual port exists:
   ```python
   python3 -c "import mido; print(mido.get_output_names())"
   ```
3. Check logs: `cat ~/.shredcli/shred.log`

### High CPU usage

Adjust the tick rate in config.json:
```json
"midi": {
  "tick_ms": 20  // Increase from 10 to 20
}
```

## Customization Ideas

### Slower Response

Increase the smoothing factor for slower BPM changes:
```json
"timing": {
  "smoothing_alpha": 0.1  // More smoothing
}
```

### Longer Idle Timeout

Wait longer before slowing down:
```json
"timing": {
  "idle_threshold_seconds": 5.0
}
```

### Different Velocity Curves

Adjust velocity ranges per voice:
```json
"velocity": {
  "bass": {"min": 100, "max": 127},
  "mid": {"min": 70, "max": 90},
  "treble": {"min": 80, "max": 110}
}
```
