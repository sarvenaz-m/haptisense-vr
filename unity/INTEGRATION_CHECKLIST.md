# Unity integration checklist

Use this checklist after importing `Assets/HaptiSense` into a Unity project.
It defines the evidence needed before describing the Unity path as runnable or
device-validated.

## Editor integration

- [ ] Record the Unity editor and target-platform versions.
- [ ] Confirm `HaptiSense.Runtime` compiles without Console errors.
- [ ] Add `HapticContactPublisher` to a Rigidbody tool with a Collider.
- [ ] Add `HapticCommandReceiver` to a persistent scene object.
- [ ] Add a Collider to the virtual contact surface.
- [ ] Start `haptisense bridge` and enter Play mode.
- [ ] Confirm packets travel on loopback ports 9051 and 9050.
- [ ] Capture a short screen recording showing contact and the command visualiser.

## Hardware extension

- [ ] Keep the device's calibrated high-rate servo in its supported SDK.
- [ ] Map `LatestCommand` to an explicit device adapter.
- [ ] Add a physical emergency stop and device-specific output bounds.
- [ ] Measure end-to-end latency, jitter, update rate, and dropped packets.
- [ ] Record calibration procedure, device model, firmware, and driver version.
- [ ] Obtain the required ethics and safety approvals before participant use.

Until these checks are completed, this folder is evidence of an inspectable
Unity integration design and import-ready C# source—not a validated Unity scene
or haptic-device implementation.
