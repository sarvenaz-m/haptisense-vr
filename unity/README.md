# Unity integration example

## v0.3 desktop replay scene

1. Create a desktop Unity project using a built-in or URP lit renderer.
2. Copy `Assets/HaptiSense` into its `Assets/` directory.
3. Export `session.json` from `haptisense research`. Copy it to
   `Assets/HaptiSense/Data/default-session.json` (create `Data` first).
4. Choose **HaptiSense > Create desktop replay scene**. The tool asks to save any
   modified scene first and creates a new empty scene with the replay component.
5. Save the scene, enter Play Mode and use Play/Pause and the timeline. The
   runtime creates the surface mesh, probe, lighting, camera and numerical HUD.

This scene replays exported Python/browser traces; it does not independently
compute the contact model or demonstrate C# numerical parity. The data loader
validates the schema, evidence label, sample count, time grid and bounded values.
It is a desktop computational replay, with no XR tracking or actuator output.
**Unity Editor execution has not been verified in the recorded environment.**
Preserve the Unity version, Console log and your actual screen recording if you
execute it. The original UDP source examples remain available below.

This folder contains a minimal engine-side integration for the Python bridge.
It is deliberately source-only so reviewers can inspect the C# without a large
binary Unity project. The assembly definition makes the scripts import-ready,
but this repository does not claim a verified build in a particular Unity
editor version.

## Scene setup

1. Copy `Assets/HaptiSense` into a Unity project.
2. Add `HapticCommandReceiver` to an empty persistent GameObject.
3. Add a Rigidbody, Collider, and `HapticContactPublisher` to the virtual tool.
4. Ensure the tissue/surface has a Collider.
5. Start `haptisense bridge` before entering Play mode.

The publisher sends contact state to UDP port 9051. The receiver listens for
safety-limited commands on port 9050. Both use loopback by default.

Complete the [integration checklist](INTEGRATION_CHECKLIST.md) and retain the
editor version, Console output, and a short scene recording before presenting
this path as a runnable Unity demonstration.

## Important limitation

Unity's physics loop is not a replacement for a dedicated high-rate haptic
servo loop. For a Phantom/Geomagic or equivalent device, keep the calibrated
device loop inside its supported SDK or middleware and use this bridge for
scene state, visualization, logging, and supervisory commands.
