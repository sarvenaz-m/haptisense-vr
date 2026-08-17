# Grant evidence matrix

This document helps a reviewer distinguish implemented evidence, prior
experience, and future laboratory validation. The project is supplementary
portfolio evidence; it does not replace academic records or proof of historical
employment.

## Selection-criterion mapping

| Selection criterion | Weight in the call | Repository evidence | Defensible application wording | Remaining gap |
|---|---:|---|---|---|
| Academic curriculum and grades | 30% | Not addressed by software | Use official degrees, transcripts, enrolment, publications, and grades | Repository cannot improve or replace academic records |
| Prior VR and haptics development | 40% | Interactive demonstrator, Unity C#, force/vibration models, UDP bridge | “I developed a current reproducible demonstrator and can explain each module.” | Historical claims still require genuine AKO or other records |
| Physics-based animation / haptic interaction | 20% | Kelvin–Voigt contact, friction, filtered inertial cue, multimodal mapping, safety layer | “I implemented compliant contact and safety-gated multimodal cue synthesis.” | Device calibration and experimental comparison remain future work |
| Motivation and English | 10% | Research questions, documentation, limitations, extension plan | “I created a tailored but independently scoped demonstrator to show day-one readiness.” | Evaluated from the letter/interview, not code alone |

## Work-plan mapping

### T2 — Force interaction without a fixed substrate

**Implemented**

- `BodyGroundedInertialCue` estimates apparent reaction from acceleration.
- A one-pole filter suppresses rapid noise.
- Maximum force is clamped before downstream output.
- The interactive site exposes the force response to parameter changes.

**What it proves**

- understanding of transient inertial/body-grounded feedback;
- ability to translate a physical hypothesis into testable code;
- awareness that substrate-free feedback cannot generate arbitrary sustained force.

**Not yet proved**

- actuator output, comfort, perception, latency, or wearability.

### T3 — Force and cutaneous feedback for surgical simulation

**Implemented**

- Kelvin–Voigt tissue response;
- regularized Coulomb friction;
- soft, fibrous, and membrane texture profiles;
- contact-load- and scan-speed-dependent vibration;
- force, slew, frequency, and amplitude safety limits.

**What it proves**

- physics-based interaction modelling;
- multimodal cue design;
- software separation suitable for later device calibration.

**Not yet proved**

- tissue-phantom fit, perceived realism, or surgical training validity.

### T4 — Visual and haptic perceptual acuity

**Implemented**

- two-alternative forced-choice design;
- two-down/one-up staircase;
- deterministic synthetic observer;
- reversal-based threshold estimate;
- structured CSV/JSON output;
- ethics, calibration, counterbalancing, stopping, and analysis plan.

**What it proves**

- ability to design and program a formal psychophysical workflow;
- separation of synthetic pipeline checks from human-subject evidence.

**Not yet proved**

- recruitment, ethics approval, real participant thresholds, or inferential results.

## Evidence hierarchy for the application

Use evidence in this order:

1. Official academic and employment documents.
2. Authentic dated AKO material and references.
3. This current GitHub demonstrator as inspectable technical evidence.
4. A concise explanation of the next laboratory validation step.

The repository is strongest when it supports an already truthful narrative. It
is weakest when used as a substitute for missing historical evidence.

## Recommended one-sentence positioning

> To provide inspectable evidence of my current readiness, I developed
> HaptiSense VR, an independent reproducible demonstrator integrating compliant
> contact physics, body-grounded inertial cues, force–vibration synthesis,
> Unity–Python communication, safety gating, and adaptive psychophysics.
