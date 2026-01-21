# Critical Bug Fixes Report
**Date:** 2026-01-21
**Author:** Claude Code

## Summary

Fixed 3 critical issues and implemented extended frequency range support for the serial protocol.

---

## Changes Made

### 1. Extended Frequency Range (Feature)

**Problem:** Audio frequency was limited to 1 byte (0-255 Hz), insufficient for audible range (20-20000 Hz).

**Solution:** Extended frequency to 2 bytes (uint16, 0-65535 Hz) across the entire protocol.

**Files Modified:**
- `app/python/core/arduino_communication.py` - Encode frequency as 2 bytes little-endian
- `code/arduino/arduino.ino` - Parse 2-byte frequency, use `tone()` for proper audio generation
- `code/teensy/teensy.ino` - Parse 2-byte frequency with division-by-zero protection
- `CLAUDE.md` - Updated protocol documentation

**New Protocol Format:**
```
Commands (5 bytes payload):
  'v'/'w'/'b': [amp:1] [freq:2] [duration:2]

Combined (10 bytes payload):
  'c': [ampV:1] [freqV:2] [durV:2] [ampB:1] [freqB:2] [durB:2]
```

---

### 2. Buffer Overflow Fix (Critical)

**Problem:** Serial read didn't validate message length before reading into 64-byte buffer. Malformed packets with `len > 64` caused buffer overflow.

**Solution:** Added bounds check before reading payload.

**Files Modified:**
- `code/arduino/arduino.ino:134-139`
- `code/teensy/teensy.ino:144-149`

**Code Added:**
```cpp
if (len > sizeof(buff)) {
    while (Serial.available()) Serial.read(); // flush invalid data
    return;
}
```

---

### 3. Race Condition Fix (Critical)

**Problem:** `self.running`, `self.current_idx`, and `self.sequence` were accessed from multiple threads (UI and worker) without synchronization, causing potential data corruption.

**Solution:**
- Added `threading.Lock()` to protect all shared state
- Implemented thread-safe properties for `running`, `current_idx`, `sequence`
- Made worker thread a daemon with `join(timeout=2.0)`
- Copy sequence before iteration in main loop

**File Modified:** `app/python/core/experiment.py:26-95`

---

### 4. JSON Validation Fix (Critical)

**Problem:** JSON parsing assumed all fields existed without validation. Missing fields caused `KeyError` at runtime. Bare `except:` clause caught `KeyboardInterrupt` and `SystemExit`.

**Solution:**
- Added validation for required fields with descriptive `ValueError` messages
- Used `.get()` with defaults for optional fields
- Replaced bare `except:` with specific exception types
- Added `max(0, dt)` to prevent negative delays

**File Modified:** `app/python/core/experiment.py:96-220`

**Validation Added For:**
| Type | Required Fields |
|------|-----------------|
| Sequence | `Repeat`, `Content` |
| Buzzer | `Amplitude` |
| Vib1/Vib2 | `Amplitude`, `Frequency`, `Duration` |
| BuzzVib1 | `Amplitude_vib1`, `Frequency_vib1`, `Duration_vib1`, `Amplitude_buzz` |
| Delay | `Duration` |
| Dropout_sequence | `Number_drop`, `Repeat`, `Content`, `Dropout_content` |

---

### 5. Amplitude Overflow Fix (High)

**Problem:** Amplitude values > 1.0 caused `OverflowError` when converting to single byte.

**Solution:** Added clamping in `arduino_communication.py`:
```python
amp = int(max(0, min(255, signal[1]*255))).to_bytes(1, ...)
```

**File Modified:** `app/python/core/arduino_communication.py:35-52`

---

## Testing Notes

- **Breaking change:** Firmware must be reflashed for new 2-byte frequency protocol
- Python and firmware changes must be deployed together
- Existing JSON experiment files remain compatible (no schema changes)

---

## Files Changed

| File | Type | Changes |
|------|------|---------|
| `app/python/core/arduino_communication.py` | Modified | 2-byte freq, amplitude clamping |
| `app/python/core/experiment.py` | Modified | Thread safety, JSON validation |
| `code/arduino/arduino.ino` | Modified | 2-byte freq, buffer check, tone() |
| `code/teensy/teensy.ino` | Modified | 2-byte freq, buffer check |
| `CLAUDE.md` | Modified | Protocol documentation |
| `ISSUES.md` | Created | Bug tracking document |
