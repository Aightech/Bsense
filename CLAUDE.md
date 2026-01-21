# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bsense is a device for triggering audio and haptic stimuli for prenatal studies. It consists of:
- **Python GUI application** (`app/python/`) - Control interface using CustomTkinter
- **Firmware** (`code/`) - Arduino Mega 2560 and Teensy 4.x implementations
- **Hardware** - LRA vibration motors, buzzer, H-bridge driver (~£70 total cost)

## Common Commands

### Running the Python GUI
```bash
cd app/python
source bsense_env/bin/activate  # Linux/macOS
python main.py
```

CLI flags:
- `-d` - Debug mode
- `-p <port>` - Serial port (default: COM3, use `/dev/ttyUSB0` on Linux)
- `-f <file>` - Load experiment JSON file

### Dependencies
```bash
pip install customtkinter pyserial
```

### Running Tests
```bash
cd app/python
python -m unittest discover tests/
```

### Firmware
Compile with Arduino IDE or VS Code Arduino extension. Target boards: Arduino Mega 2560 or Teensy 4.0/4.1.

## Architecture

### Python Application (`app/python/`)

**Entry point**: `main.py` → launches `BsenseGUI()`

**Core modules**:
- `core/experiment.py` - `Experiment` class parses JSON protocols and executes stimuli in background thread via callbacks
- `core/arduino_communication.py` - `ArduinoCom` class handles serial protocol (115200 baud, binary format)
- `ui/main_window.py` - CustomTkinter GUI with connection, experiment selection, and logging panels

**Data flow**: JSON protocol → `Experiment.__read_type()` recursive parser → `ArduinoCom.send_signal()` → serial to device

### Serial Protocol

Binary format starting with `0xaa` header:
```
[0xaa] [cmd] [len] [payload...]

Commands (5 bytes payload):
  'v' - Vibration 1: [amp:1] [freq:2] [duration:2]
  'w' - Vibration 2: [amp:1] [freq:2] [duration:2]
  'b' - Buzzer:      [amp:1] [freq:2] [duration:2]

Combined (10 bytes payload):
  'c' - Vib+Buzz: [ampV:1] [freqV:2] [durV:2] [ampB:1] [freqB:2] [durB:2]
```

- Amplitude: float 0-1 → uint8 0-255
- Frequency: uint16 little-endian (0-65535 Hz)
- Duration: uint16 little-endian (milliseconds)

### Experiment Protocol (JSON)

Hierarchical structure with types:
- `Sequence` - Repeatable block with `Repeat` count and `Content` array
- `stimulus` - Container for simultaneous stimuli (`Vib1`, `Vib2`, `Buzzer`, `BuzzVib1`)
- `Delay` - Pause with `Duration` (seconds) and optional `Deviation`
- `Dropout_sequence` - Random dropout patterns for variability

Examples in `app/python/config/*.json`

### Firmware (`code/`)

Timer-interrupt driven signal generation:
- `arduino/arduino.ino` - Arduino Mega version
- `teensyA/teensyA.ino` - Teensy version with microsecond timing

Both use same serial protocol and PWM for motor/buzzer control.

## Key Files

| Path | Purpose |
|------|---------|
| `app/python/core/experiment.py` | Protocol parser and executor |
| `app/python/core/arduino_communication.py` | Serial communication |
| `app/python/ui/main_window.py` | GUI implementation |
| `app/python/config/*.json` | Experiment definitions |
| `code/teensyA/teensyA.ino` | Teensy firmware |
| `userManualGUI.md` | JSON protocol format specification |
