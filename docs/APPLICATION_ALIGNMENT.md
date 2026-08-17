# Application alignment and honest positioning

## Purpose

This repository is a current, independent portfolio prototype designed to make
technical capability inspectable. It is not evidence that every component was
previously deployed at AKO, and it is not an official deliverable of any grant.

## Mapping to the research tasks

| Research task | Implemented demonstration | Next empirical step |
|---|---|---|
| Force feedback without a fixed substrate | Filtered apparent reaction from controller/hand acceleration; body-grounded command path | Connect an inertial or wearable actuator and quantify achievable impulse, latency, and comfort |
| Force plus cutaneous feedback for surgery | Compliant force model, friction, texture-dependent vibration, safety-gated command | Calibrate against tissue phantoms and compare unimodal vs multimodal conditions |
| Visual and haptic acuity in VR | 2AFC two-down/one-up staircase, structured trial log, threshold estimate | Ethics approval, preregistration, participant recruitment, and inferential analysis |

## Mapping to the selection criteria

The call assigns 40% to prior VR/haptics development and 20% to physics-based
animation or haptic interaction. Reviewers should therefore reach the working
code quickly. Suggested evidence order:

1. README overview and generated trace.
2. `force_models.py` and `cues.py` for scientific reasoning.
3. `unity/` and `bridge.py` for C#/Python integration.
4. `psychophysics.py` and `EXPERIMENT_PROTOCOL.md` for experimental competence.
5. tests and CI for software quality.

## Recommended CV entry

**HaptiSense VR — Independent Haptic Research Prototype | 2026**  
Python, C#, Unity integration, physics-based simulation, psychophysics

- Developed a modular prototype combining compliant contact force, body-grounded inertial cues, and texture-dependent vibrotactile feedback for immersive surgical interaction.
- Implemented a safety-gated Unity/Python interface and device-agnostic hardware abstraction for future Phantom/Geomagic or wearable-actuator integration.
- Implemented a reproducible 2AFC adaptive-staircase pipeline for visual and haptic discrimination, with synthetic data clearly separated from future participant studies.
- Added automated tests, deterministic outputs, structured logs, and a formal human-study protocol.

## Suggested motivation-letter sentence

> To demonstrate how I would contribute from the first day, I developed
> HaptiSense VR, an independent and reproducible portfolio prototype that links
> compliant contact physics, body-grounded inertial cues, force–vibration
> synthesis, Unity integration, and adaptive psychophysics in one testable
> architecture.

## Suggested interview explanation

> My AKO experience taught me to connect healthcare requirements, sensing,
> electronics, and real-time software. In this portfolio project I made that
> systems-level approach explicit: the scientific models are separated from the
> safety layer and the device transport, and the psychophysical method produces
> structured trial records. The committed results are synthetic; my next step
> with laboratory access would be device calibration, latency characterization,
> ethics approval, and a preregistered participant study.

## AKO background connection

Only include statements that can be supported in an interview or with records.
The strongest defensible bridge is:

- smart-healthcare product context;
- non-invasive monitoring and wearable-sensing concepts;
- coordination between electronics and software;
- real-time application development and device communication;
- quantitative biomedical-data analysis and EEG experience;
- startup prototyping under practical constraints.

If specific Phantom, Unity, surgical-simulation, or participant-study work was
completed at AKO, keep supporting material ready: screenshots, code history,
device photographs, protocols, reports, named collaborators, or a reference who
can confirm the work.

## Claims not to make yet

Do not say any of the following unless separately verified:

- “validated on a Phantom/Geomagic device”;
- “tested at 1 kHz on hardware”;
- “clinically validated surgical simulator”;
- “human study completed”;
- “statistically significant improvement”;
- “HIITS/INESC-ID project deliverable”;
- “original AKO repository” or a date earlier than the actual creation date.

Accurate wording is stronger than inflated wording because it lets the reviewer
see exactly what is implemented and what would be done next in the laboratory.
