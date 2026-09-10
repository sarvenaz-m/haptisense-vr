# Bench validation and honest evidence capture

Status: source template + computational tests. No physical experiment has been
performed by the authoring assistant. No Unity Editor build has been verified.
This extension is NOT a complete VR device or a validated force-feedback rig.

## 1. Run the verified software path first

From the project root, with Python 3.10+ and Node.js for existing parity tests:

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/reproduce_evidence.py --output results/my_first_review
```

The C++ firmware-logic test needs g++; it reports SKIPPED if absent. The script
produces all simulation CSV/JSON/SVG files, raw benchmark repetitions, test log
and SHA-256 source hashes. A new output path is required on every invocation.
The initial review results are under `results/review_2026-09-05`.

## 2. Unity desktop scene (user execution required)

1. Create an empty 3D Unity project; record the exact Editor version.
2. Copy `unity/Assets/HaptiSense` into its `Assets` directory.
3. Create empty object `BenchLink`; add `BenchContactSweep` and
   `HapticCommandReceiver`. Do not also attach the collision publisher.
4. Create a small sphere and assign it as `visualTool` on the sweep component.
   Add a plane at y=0 and a camera viewing the tool/plane; scale is in metres.
5. Set Project Settings > Time > Fixed Timestep to 0.02 seconds (nominal 50 Hz).
   This is not a 500 Hz hardware servo or a real-time guarantee.
6. Run `python -m haptisense.bench --output results/unity_mock_01.csv --seconds 60`.
7. Enter Play mode; enable `Enable Synthetic Contact` on the sweep component.
8. Verify the CSV contains accepted packets, nonzero duty commands during contact
   and zero duty during the lift-off interval. Switch contact off and verify zero.
9. Stop Play mode while bridge remains open; verify zero requested PWM after stale
   timeout. Save Console output, Editor version, video and exact source hash.

This scene uses mathematically generated motion, not tracked hands or a headset.
Use `HapticContactPublisher` separately for collision-driven input; test the
appropriate Rigidbody API for your Editor version. The original C# uses
`Rigidbody.velocity`; newer versions may recommend `linearVelocity`.
Do not call Python-JavaScript parity a Python-Unity parity test: only the former
has actually run. A Unity run needs its own recorded validation.

## 3. Conditional low-voltage ERM bench wiring

Do not purchase or wire parts until the exact motor/board/driver ratings are
known. The supplied sketch targets Arduino UNO R3 (ATmega328P), NOT ESP32 or LRA.
For an LRA use a suitable driver and a different adapter; do not connect it to
this ERM MOSFET circuit. A knowledgeable electronics reviewer should check the
assembled circuit before applying power. This is a tabletop demo; no body mount,
servo force rig, medical use, or participant exposure is authorized by this guide.

| Connection | Design intent / constraint |
|---|---|
| UNO D9 -> gate resistor -> logic-level N-MOSFET gate | PWM; resistor and MOSFET selected for rated motor/current and 5 V logic |
| Gate -> pull-down -> source/GND | Keeps driver off during reset; typical starting value 10 kOhm, verify |
| Source -> common GND | Common ground with UNO and rated motor supply |
| Drain -> ERM negative | Never drive the motor directly from GPIO |
| ERM positive -> fused, current-limited rated supply | Match the actual motor voltage; do not assume 5 V is safe for a 3 V motor |
| Flyback diode across ERM | Cathode to motor positive, anode to drain; suitable current rating |
| UNO D2 -> normally-open ARM switch -> GND | Open disables output; physical power cut must remain available |
| A0 -> known voltage divider / sensor -> GND | 0..5 V only; ground A0 if unused; no floating reading interpreted as force |

Select decoupling, fuse, supply and driver from their actual datasheets. Never
connect the assembly to mains. The 64/255 PWM cap is a conservative *software
design choice*, not proof of electrical, thermal or physiological safety.
An ERM maps PWM duty imperfectly to vibration amplitude; mechanical frequency
is coupled to speed. The software's requested frequency is NOT implemented by
this adapter. The `fx/fy/fz` model is NOT converted to physical Newtons.

## 4. Firmware, transport and stop tests

1. With motor power disconnected and ARM open, compile/upload
   `firmware/uno_erm_bench/uno_erm_bench.ino` for UNO. Record IDE/core version and
   build log. The host C++ test is not a substitute for this AVR compilation.
2. Verify startup/reset output is off. Verify bootloader/watchdog compatibility.
3. Install optional transport dependency: `python -m pip install pyserial`.
4. Discover the actual port: `python -m serial.tools.list_ports`.
5. Run, substituting the real port (example only):

```bash
python -m haptisense.bench --serial-port COM3 --arm-bench --seconds 30 --output results/physical_bench_01.csv
```

6. First keep ARM open. Confirm `ack_pwm=0`. Then, after electrical review, use
   the switch during a brief tabletop test. Observe actual output with appropriate
   measurement equipment. Never trust an acknowledgement alone as motor motion.
7. Test disabling contact, closing Unity, closing Python, serial disconnection,
   malformed commands and opening ARM. Keep a manual power cut within reach.
8. Firmware command timeout is 150 ms, host stale-input timeout is 100 ms, and
   MCU watchdog nominally 250 ms. These are design values, NOT measured cessation
   times: buffering, firmware execution, motor inertia and hardware affect stops.

Protocol at 115200 baud, ASCII lines:

```text
H1,sequence,pwm\n
A1,sequence,applied_pwm,adc_raw,device_ms\n
```

Commands require unsigned sequence 0..2147483647 and PWM 0..64. Invalid firmware
input stops output. Long lines are discarded until newline. Missing/invalid host
ack terminates the session and attempts zero output; device timeout is still
necessary if the stop command is not delivered. Device timestamps wrap; do not
subtract them from host monotonic timestamps.

## 5. What each measurement actually means

- `serial_roundtrip_ms`: time on the host from serial write to matching ack. It
  includes communication/firmware/host scheduling. Not actuator onset latency.
- `adc_raw`: uncalibrated 10-bit reading. Not Newtons, pressure or acceleration.
- `ack_pwm`: firmware-reported duty command. Not a measured physical stimulus.
- `physical_serial_ack`: real serial communication, not proof of motor movement.
- `mock_no_hardware`: no serial hardware was accessed. Never relabel this column.

True force needs known reference loads, calibration curve, residual error,
repeatability and uncertainty. True vibration needs suitable accelerometer/
measurement bandwidth and sample rate. Onset latency needs synchronized trigger
and sensor observations. Keep commanded and measured values in separate columns.

## 6. Two-minute video and evidence bundle

0:00 identify yourself, date, commit and exact device; 0:15 show real wiring and
open ARM; 0:30 show Unity and physical response simultaneously; 1:00 demonstrate
contact/lift-off; 1:20 close Unity and demonstrate stop; 1:40 show CSV and explain
what is commanded vs measured. Do not edit together different trials as one run.
Save video, circuit photo, BOM/datasheets, build log, CSV, device information,
raw measurement recordings and limitations. Do not create a fictitious video.

## 7. Release, privacy and applicant ownership

Review each changed file; run it locally; explain every equation and failure
mode in your own words. The September extension was prepared with AI assistance;
do not claim independent physical development or experiments you did not do.
Original source has been retained from commit `13d65e03220be16da0c27b022c58749cc82272d4`.

Upload code only, NOT the private application folder, grades, residence ID,
enrolment certificate, phone or signatures. From a clean clone of your own repo,
copy only extension files listed in `docs/REVIEW_RELEASE.md`, review `git diff`,
run tests and commit on a new branch. Nothing in this delivery is pushed.
