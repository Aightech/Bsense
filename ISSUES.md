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

### ~~9. GUI Updates from Worker Thread~~ (FIXED)
**File:** `app/python/ui/main_window.py`
~~**Description:** Tkinter not thread-safe, GUI updates from worker thread.~~
**Fix applied:** Used `after()` to schedule `add_log` and `on_new_event` GUI updates on main thread.

### ~~10. Empty Sequence Index Error~~ (FIXED)
**File:** `app/python/ui/main_window.py`
~~**Description:** `IndexError` if sequence empty or index out of bounds.~~
**Fix applied:** Added bounds check in `_update_treeview_selection()`.

### ~~11. Bare Except Clause~~ (FIXED)
**File:** `app/python/core/experiment.py`
~~**Description:** Catches too many exceptions.~~
**Fix applied:** Now catches `FileNotFoundError`, `json.JSONDecodeError`, `ValueError` specifically.

### ~~12. Non-Daemon Thread Blocks Exit~~ (FIXED)
**File:** `app/python/core/experiment.py`
~~**Description:** Thread prevents Python exit.~~
**Fix applied:** Thread set to `daemon=True`, `join()` has timeout.

### ~~13. Negative Delay Possible~~ (FIXED)
**File:** `app/python/core/experiment.py`
~~**Description:** Deviation could cause negative delay.~~
**Fix applied:** Added `dt = max(0, dt)` clamping.

### ~~14. micros() Overflow After ~70 Minutes~~ (FIXED)
**File:** `code/arduino/arduino.ino`
~~**Description:** Timing comparisons fail after overflow.~~
**Fix applied:** Changed to `(t_us - start_time) >= duration` pattern with separate start/duration variables.

### ~~15. Blocking Serial Read~~ (FIXED)
**File:** `code/arduino/arduino.ino`, `code/teensy/teensy.ino`
~~**Description:** Serial.readBytes blocks indefinitely.~~
**Fix applied:** Added 100ms timeout with `millis()` check before reading payload.

### ~~16. No Message Length Validation~~ (FIXED)
**File:** `code/arduino/arduino.ino`, `code/teensy/teensy.ino`
~~**Description:** No validation of expected message length per command.~~
**Fix applied:** Added expected length validation (5 for v/w/b, 10 for c) before processing.

### ~~17. Unvalidated Signal Format~~ (FIXED)
**File:** `app/python/core/arduino_communication.py`
~~**Description:** Assumes tuple structure without checking.~~
**Fix applied:** Added validation for signal type, tuple length, and element count per command type.

---

## Low Severity

### ~~18. Hardcoded COM3 Port~~ (FIXED)
**File:** `app/python/ui/main_window.py`
~~**Description:** Default "COM3" fails on Linux/Mac.~~
**Fix applied:** Platform detection using `sys.platform` - COM3 (Windows), /dev/ttyUSB0 (Linux), /dev/tty.usbmodem* (Mac).

### ~~19. No Connection Retry Logic~~ (FIXED)
**File:** `app/python/core/arduino_communication.py`
~~**Description:** Single failed connection attempt exits immediately.~~
**Fix applied:** Added `retries` and `retry_delay` parameters with exponential backoff (default: 3 retries).

### ~~20. Print Statements Instead of Logging~~ (FIXED)
**File:** `app/python/core/arduino_communication.py`, `app/python/ui/main_window.py`, `app/python/main.py`
~~**Description:** Debug output goes to stderr, not captured in log files.~~
**Fix applied:** Replaced all print() with logging module. Configured in main.py with DEBUG level when -d flag used.

### ~~21. Duplicate Import~~ (FIXED)
**File:** `app/python/ui/main_window.py`
~~**Description:** `import tkinter as tk` appears twice.~~
**Fix applied:** Removed duplicate imports, cleaned up import section.

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
