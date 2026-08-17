# Unity integration example

This folder contains a minimal engine-side integration for the Python bridge.
It is deliberately source-only so reviewers can inspect the C# without a large
binary Unity project.

## Scene setup

1. Copy `Assets/HaptiSense` into a Unity project.
2. Add `HapticCommandReceiver` to an empty persistent GameObject.
3. Add a Rigidbody, Collider, and `HapticContactPublisher` to the virtual tool.
4. Ensure the tissue/surface has a Collider.
5. Start `haptisense bridge` before entering Play mode.

The publisher sends contact state to UDP port 9051. The receiver listens for
safety-limited commands on port 9050. Both use loopback by default.

## Important limitation

Unity's physics loop is not a replacement for a dedicated high-rate haptic
servo loop. For a Phantom/Geomagic or equivalent device, keep the calibrated
device loop inside its supported SDK or middleware and use this bridge for
scene state, visualization, logging, and supervisory commands.
