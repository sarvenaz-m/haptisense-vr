# 90-second reviewer demo

This script gives a concise, technically honest tour of HaptiSense VR.

## 0–15 seconds — research question

> HaptiSense VR is an independent research demonstrator for three connected
> problems: transient force cues without a fixed substrate, force plus
> vibrotactile surgical contact, and visual/haptic acuity measurement.

Show the repository hero and the research-integrity statement.

## 15–40 seconds — interactive physics

Open the GitHub Pages demonstrator.

The displayed default metrics are produced by the same 500 Hz vector model as
the Python simulation; parity is checked automatically in CI.

1. Select **Soft tissue**.
2. Increase stiffness from 650 to approximately 1,000 N/m.
3. Observe peak/RMS force increase.
4. Increase roughness and scan speed.
5. Observe vibration amplitude/frequency response.
6. Select **Fibrous tissue** and point to safety interventions.

Say:

> The model combines Kelvin–Voigt contact, regularized friction, filtered
> inertial reaction, texture-dependent vibration, and a stateful safety layer.

## 40–60 seconds — implementation path

Open:

- `src/haptisense/force_models.py`;
- `src/haptisense/cues.py`;
- `unity/Assets/HaptiSense/Scripts/`;
- `src/haptisense/bridge.py`.

Say:

> Scientific models are independent of Unity and proprietary hardware. Unity
> publishes contact state, Python computes the cue, and the safe command is
> available to a future device-specific adapter.

## 60–78 seconds — psychophysics

Show the staircase chart and `results/psychophysics/summary.json`.

> The 2AFC two-down/one-up pipeline generates structured trials and reversal
> thresholds. The committed observer is explicitly synthetic; real recruitment
> requires ethics approval, calibration, and preregistration.

## 78–90 seconds — validation and next step

Show the passing CI/tests.

> Seventeen tests verify force response, friction direction, cue bounds, safety,
> reproducibility, browser/Python parity, documentation links, and bridge
> behaviour. My next laboratory step is device
> calibration, latency/jitter characterisation, and a preregistered user study.

## Do not say

- that a Phantom/Geomagic device has already been validated;
- that the 500 Hz Python demo is a measured hardware servo rate;
- that the synthetic thresholds came from participants;
- that this repository was created at AKO or by INESC-ID.
