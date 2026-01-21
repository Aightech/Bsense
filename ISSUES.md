# Known Issues and Limitations

This document tracks bugs, limitations, and potential improvements in the Bsense codebase.

## Critical Issues

### ~~1. Buffer Overflow in Serial Read~~ (FIXED)
**File:** `code/arduino/arduino.ino`, `code/teensy/teensy.ino`
~~**Description:** Serial read doesn't validate `len` before reading into 64-byte buffer.~~
**Fix applied:** Added bounds check `if (len > sizeof(buff))` before reading payload.

### ~~2. Race Conditions in Experiment Thread~~ (FIXED)
**File:** `app/python/core/experiment.py`
~~**Description:** Shared state accessed from multiple threads without synchronization.~~
**Fix applied:** Added `threading.Lock()` protecting `_running`, `_current_idx`, `_sequence`. Made thread daemon with join timeout.

### ~~3. Unvalidated JSON Parsing~~ (FIXED)
**File:** `app/python/core/experiment.py`
~~**Description:** Code assumes JSON fields exist without checking.~~
**Fix applied:** Added field validation with `.get()` for optional fields, `ValueError` exceptions for missing required fields, specific exception handling in `from_json()`.

---

## High Severity

### ~~4. Serial Port Resource Leak~~ (FIXED)
**File:** `app/python/core/arduino_communication.py`
~~**Description:** Previous connection never closed before opening new one.~~
**Fix applied:** Added `disconnect()` method, call it before new connection, catch specific exceptions.

### ~~5. Amplitude Value Overflow~~ (FIXED)
**File:** `app/python/core/arduino_communication.py`
~~**Description:** Amplitude values > 1.0 cause `OverflowError`.~~
**Fix applied:** Clamped values with `max(0, min(255, signal[1]*255))`.

### ~~6. Division by Zero in Frequency Calculation~~ (FIXED)
**File:** `code/teensy/teensy.ino`
~~**Description:** Division by zero when frequency is 0.~~
**Fix applied:** Added guard `(freqVib1 > 0) ? (1000000 / freqVib1) : 0`.

### ~~7. Flawed Frequency Toggle Logic~~ (FIXED)
**File:** `code/teensy/teensy.ino`
~~**Description:** Using wrong timestamps and potential division by zero in timer handler.~~
**Fix applied:** Added start/end time tracking, proper elapsed time calculation, half_period > 0 guards.

### ~~8. Unhandled File Write Error~~ (FIXED)
**File:** `app/python/ui/main_window.py`
~~**Description:** Log file creation fails silently if directory not writable.~~
**Fix applied:** Wrapped file operations in try-except, gracefully disable logging on error.

---

## Medium Severity

### 9. GUI Updates from Worker Thread
**File:** `app/python/ui/main_window.py` (various)
**Description:** `add_log()` called from worker thread but Tkinter isn't thread-safe. Can cause crashes or corrupted GUI.
**Fix:** Use `root.after()` to schedule GUI updates on main thread.

### 10. Empty Sequence Index Error
**File:** `app/python/ui/main_window.py:140,307,336`
**Description:** `IndexError` if `current_idx >= len(children)` or sequence is empty.
**Fix:** Add bounds check before accessing.

### 11. Bare Except Clause
**File:** `app/python/core/experiment.py:196`
**Description:** Catches `KeyboardInterrupt`, `SystemExit` making debugging difficult.
**Fix:** Catch specific exceptions: `except (IOError, json.JSONDecodeError, KeyError) as e:`

### 12. Non-Daemon Thread Blocks Exit
**File:** `app/python/core/experiment.py:36-37`
**Description:** Thread prevents Python from exiting if `close()` not called.
**Fix:** Set `daemon=True` or add timeout to `join()`.

### 13. Negative Delay Possible
**File:** `app/python/core/experiment.py:159`
**Description:** If `Deviation > Duration`, delay becomes negative.
**Fix:** Clamp: `dt = max(0, dt)`

### 14. micros() Overflow After ~70 Minutes
**File:** `code/arduino/arduino.ino:46,51,56,62`
**Description:** Timing comparisons fail after unsigned 32-bit overflow.
**Fix:** Use `(micros() - start_time) > duration` pattern.

### 15. Blocking Serial Read
**File:** `code/teensy/teensy.ino:137`
**Description:** Partial message arrival hangs entire timer loop.
**Fix:** Implement state machine or use timeout.

### 16. No Message Length Validation
**File:** `code/teensy/teensy.ino:150-177`
**Description:** Reads `buff[0..3]` without verifying `len >= 4`.
**Fix:** Validate length before accessing buffer indices.

### 17. Unvalidated Signal Format
**File:** `app/python/core/arduino_communication.py:19-68`
**Description:** Assumes tuple structure without checking length/types.
**Fix:** Validate signal structure before processing.

---

## Low Severity

### 18. Hardcoded COM3 Port
**File:** `app/python/ui/main_window.py:166`
**Description:** Default "COM3" fails on Linux/Mac.
**Fix:** Auto-detect available ports or use platform-appropriate default.

### 19. No Connection Retry Logic
**File:** `app/python/core/arduino_communication.py`
**Description:** Single failed connection attempt exits immediately.
**Fix:** Add retry with exponential backoff.

### 20. Print Statements Instead of Logging
**File:** `app/python/core/experiment.py:91,164`
**Description:** Debug output goes to stderr, not captured in log files.
**Fix:** Use `logging` module.

### 21. Duplicate Import
**File:** `app/python/ui/main_window.py:1,4`
**Description:** `import tkinter as tk` appears twice.
**Fix:** Remove duplicate.

---

## Design Limitations

### 22. No Graceful Shutdown
Stimulus continues for full duration after stop is called. Worker thread may be blocked in `time.sleep()`.

### 23. No Connection Monitoring
After initial connection, disconnected cable causes silent failures with no user feedback.

### 24. No JSON Schema Validation
Custom experiment files not validated on load - errors only appear during playback.

### 25. Empty Test Suite
Test files in `app/python/tests/` are stubs with no actual tests.

---

## Feature Requests

### ~~Extended Frequency Range~~ (IMPLEMENTED)
~~Current protocol limits frequency to 1 byte (0-255 Hz). Audio frequencies need 2 bytes to support full audible range (20-20000 Hz).~~

Protocol now uses 2-byte frequency (0-65535 Hz) for all commands.
