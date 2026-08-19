# Research-task evidence matrix

This matrix links the project's three research questions to inspectable
implementation and clearly identifies the next empirical step. It is technical
documentation, not an assessment of any application or selection criterion.

| Research question | Implemented evidence | Reproducible output | Next empirical step |
|---|---|---|---|
| Can transient body-grounded cues approximate force without a fixed substrate? | `BodyGroundedInertialCue`, vector filtering, force and slew limits | Deterministic force trace and safety-event count | Integrate a supported actuator; measure output, latency, comfort, and perceptibility |
| Can compliant force and cutaneous vibration be combined for virtual surgical contact? | Kelvin–Voigt contact, regularised friction, texture profiles, multimodal synthesis | Three-scenario force/vibration comparison | Fit parameters to tissue phantoms and compare unimodal with multimodal cues |
| Can visual and haptic discrimination be measured reproducibly? | 2AFC two-down/one-up staircase, structured trial logging, threshold analysis | Seeded synthetic trials and summary | Obtain ethics approval, preregister, recruit participants, and report uncertainty |

## Evidence locations

| Capability | Primary implementation | Supporting evidence | Boundary |
|---|---|---|---|
| Physics-based interaction | `src/haptisense/force_models.py` | `tests/test_force_models.py` | Model output; not calibrated force |
| Multimodal haptic mapping | `src/haptisense/cues.py` | `results/comparison/` | Synthetic scenarios; not tissue validation |
| Safety gating | `src/haptisense/safety.py` | tests and event counts | Software bounds; not a certified safety system |
| Unity communication path | `unity/`, `src/haptisense/bridge.py` | loopback transport tests | Source integration example; not a complete Unity project or device servo |
| Psychophysics workflow | `src/haptisense/psychophysics.py` | `results/psychophysics/` and protocol | Synthetic observer; no participant evidence |
| Browser demonstrator | `docs/assets/haptic-model.js` | automated Python–JavaScript parity test | Matches the deterministic Python model at 500 Hz |

## Interpretation

The repository supports claims about implemented software, reproducibility, and
research planning. It does not establish clinical effectiveness, human
perceptual thresholds, device performance, or historical work provenance.
