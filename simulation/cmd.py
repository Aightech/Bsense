#!/usr/bin/env python3
"""
Interactive PWM -> LRA-like resonator plot with sliders:
- PWM duty
- sigf (the "blanking" frequency you use to force PWM low for half-period)
- duration (seconds until PWM forced low)

Requires: numpy, matplotlib
Optional (recommended): scipy
    pip install scipy
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# ----------------------------
# Fixed parameters
# ----------------------------
VHI = 3.3
F_PWM = 4482.0          # Hz
FS = 200_000.0          # Hz (keep >> F_PWM)
T = 1.0                 # total simulated time (s) (keep constant; "duration" gates within this)

# LRA-like bandpass (resonator) parameters
F0 = 230.0              # Hz
Q = 6.0                 # quality factor

# Plot controls
T_ZOOM = 0.10           # seconds shown
SHOW_SPECTRUM = False   # kept off here for interactive speed

# Precompute timebase once (for speed)
N = int(np.round(T * FS))
t = np.arange(N) / FS
Nz = int(np.round(T_ZOOM * FS))
tz = t[:Nz]

# ----------------------------
# Filter design once (since F0,Q,FS fixed)
# ----------------------------
use_scipy = False
try:
    from scipy import signal
    use_scipy = True

    w0n = F0 / (FS / 2.0)
    b, a = signal.iirpeak(w0n, Q)

    # Normalize gain at f0 to ~1
    w_test = 2 * np.pi * F0 / FS
    ejw = np.exp(-1j * np.arange(len(b)) * w_test)
    H = (np.sum(b * ejw)) / (np.sum(a * ejw))
    b = b / np.abs(H)

except ImportError:
    # RBJ biquad bandpass (constant skirt gain), then normalize by Q
    w0 = 2.0 * np.pi * F0 / FS
    alpha = np.sin(w0) / (2.0 * Q)

    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha

    b0, b1, b2 = b0 / a0 / Q, b1 / a0 / Q, b2 / a0 / Q
    a1, a2 = a1 / a0, a2 / a0
    b = np.array([b0, b1, b2], dtype=float)
    a = np.array([1.0, a1, a2], dtype=float)

def lfilter_df1(b, a, x):
    """Direct-form I IIR filter (fallback when scipy is missing)."""
    y = np.zeros_like(x, dtype=float)
    x1 = x2 = 0.0
    y1 = y2 = 0.0
    b0, b1, b2 = b
    _, a1, a2 = a
    for n, x0 in enumerate(x):
        y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        y[n] = y0
        x2, x1 = x1, x0
        y2, y1 = y1, y0
    return y

# ----------------------------
# Signal generator (depends on sliders)
# ----------------------------
def synth(duty_dc, sigf, duration):
    """
    Start with constant-duty PWM at F_PWM, then:
    - force PWM to 0 for half of each period of sigf  (your test pattern)
    - force PWM to 0 after 'duration' seconds
    """
    duty = np.full_like(t, float(duty_dc))
    phase = (t * F_PWM) % 1.0
    pwm = (phase < duty).astype(np.float64) * VHI

    sigf = max(float(sigf), 1e-6)
    duration = max(float(duration), 0.0)

    # "blanking" half-period at sigf (exactly as your code)
    pwm[(t % (1.0 / sigf)) < (0.5 / sigf)] = 0.0

    # gate off after duration
    pwm[t > duration] = 0.0

    # filter
    if use_scipy:
        from scipy import signal
        y = signal.lfilter(b, a, pwm)
    else:
        y = lfilter_df1(b, a, pwm)

    return pwm, y

# ----------------------------
# Initial values (match your script)
# ----------------------------
init_duty = 0.50
init_sigf = 230.0
init_duration = 0.05

pwm, y = synth(init_duty, init_sigf, init_duration)
pwmz = pwm[:Nz]
yz = y[:Nz]

# ----------------------------
# Plot
# ----------------------------
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.25)

(line_pwm,) = ax.plot(tz * 1e3, pwmz, label="PWM (0–3.3V)")
(line_y,)   = ax.plot(tz * 1e3, yz,   label=f"After resonator ~{F0:.0f} Hz (Q={Q})")

ax.set_xlabel("Time (ms)")
ax.set_ylabel("Voltage (V) / Filter output (arb.)")
ax.set_title(f"PWM {F_PWM:.0f} Hz → LRA-like resonance {F0:.0f} Hz")
ax.grid(True)
ax.legend(loc="upper right")

# ----------------------------
# Sliders
# ----------------------------
ax_duty = plt.axes([0.10, 0.16, 0.80, 0.03])
ax_sigf = plt.axes([0.10, 0.11, 0.80, 0.03])
ax_dur  = plt.axes([0.10, 0.06, 0.80, 0.03])

s_duty = Slider(ax_duty, "Duty", 0.0, 1.0, valinit=init_duty, valstep=0.001)
s_sigf = Slider(ax_sigf, "sigf (Hz)", 1.0, 1000.0, valinit=init_sigf, valstep=1.0)
s_dur  = Slider(ax_dur,  "duration (s)", 0.0, T, valinit=init_duration, valstep=0.001)

# Reset button
ax_reset = plt.axes([0.82, 0.01, 0.16, 0.035])
btn_reset = Button(ax_reset, "Reset")

def update(_=None):
    duty_dc = s_duty.val
    sigf = s_sigf.val
    duration = s_dur.val

    pwm, y = synth(duty_dc, sigf, duration)
    line_pwm.set_ydata(pwm[:Nz])
    line_y.set_ydata(y[:Nz])

    # Optional: keep y-limits reasonable as you sweep parameters
    ax.relim()
    ax.autoscale_view()

    fig.canvas.draw_idle()

def on_reset(event):
    s_duty.reset()
    s_sigf.reset()
    s_dur.reset()

s_duty.on_changed(update)
s_sigf.on_changed(update)
s_dur.on_changed(update)
btn_reset.on_clicked(on_reset)



plt.show()

# ============================================================
# Average peak-to-peak amplitude vs PWM duty sweep
# ============================================================
plt.figure()

for sigf_val in range(100, 501, 50):
    DUTY_VALUES = np.arange(0.0, 1.01, 0.1)
    sigf = sigf_val#230.0       # Hz (same as before)
    duration = 0.05    # seconds
    discard_cycles = 2 # ignore initial transient cycles

    def avg_peak_to_peak(y, t, sigf, duration):
        """Compute average peak-to-peak amplitude over cycles."""
        T_sig = 1.0 / sigf
        valid = t <= duration
        yv = y[valid]
        tv = t[valid]

        n_cycles = int((tv[-1] - tv[0]) / T_sig)
        pp_vals = []

        for k in range(discard_cycles, n_cycles):
            t0 = k * T_sig
            t1 = (k + 1) * T_sig
            idx = (tv >= t0) & (tv < t1)
            if np.any(idx):
                seg = yv[idx]
                pp_vals.append(seg.max() - seg.min())

        return np.mean(pp_vals) if pp_vals else 0.0

    pp_results = []

    for duty in DUTY_VALUES:
        # regenerate PWM
        duty_arr = np.full_like(t, duty)
        phase = (t * F_PWM) % 1.0
        pwm = (phase < duty_arr).astype(float) * VHI

        # same gating logic as before
        pwm[(t % (1 / sigf)) < (0.5 / sigf)] = 0.0
        pwm[t > duration] = 0.0

        # filter
        if use_scipy:
            from scipy import signal
            y = signal.lfilter(b, a, pwm)
        else:
            y = lfilter_df1(b, a, pwm)

        pp = avg_peak_to_peak(y, t, sigf, duration)
        pp_results.append(pp)

    pp_results = np.array(pp_results)

    plt.plot(DUTY_VALUES, pp_results, marker="o", label=f"sigf={sigf_val} Hz")

plt.xlabel("PWM duty cycle")
plt.ylabel("Average peak-to-peak amplitude (arb.)")
plt.title("LRA response vs PWM duty")
plt.legend()
plt.grid(True)
plt.show()
