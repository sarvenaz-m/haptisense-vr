# A five-minute technical review

1. Serve `docs/` and open `workbench.html`. The initial paused position is in
   contact. Inspect command magnitude, equilibrium force, memory and friction.
2. Press Play. During the hold, penetration remains fixed while the SLS memory
   branch decays. Scrub to compare the beginning and end of the hold.
3. Switch to Model comparison. The elastic and approach-damped Kelvin responses
   share the same equilibrium hold force; the SLS transient relaxes toward it.
   Inspect the force/penetration loops and command limiting separately.
4. Change only stiffness. Explain the result with `k(d + βd³)`. Change scan speed
   to zero and observe that cutaneous amplitude vanishes. Rotate the surface
   to inspect the illustrative geometry.
5. Export a session JSON and CSV. Import the JSON; the model recomputes the
   results. Compare the CSV with `python -m haptisense research` at matching
   settings. Python/JavaScript parity covers every sample field for six runs.
6. Open Perceptual protocol. Explain why the committed synthetic staircase is
   a pipeline rehearsal, and what would be required for a real study.

## Relationship to the intended research work

| Area | Current evidence | Next empirical step |
|---|---|---|
| Physics / haptic interaction | Explicit constitutive equations, relaxation, friction, analytical tests, parameter-identification self-check | Calibrated contact measurements and model selection |
| Force + cutaneous cues | Numerical vector force and vibration commands with traces | Characterize actuator bandwidth, latency and cue coupling |
| VR development | Desktop scene builder, C# source, UDP interface, interactive browser renderer | Execute Unity; integrate tracked motion; evaluate device SDK |
| Perceptual methods | Synthetic two-down/one-up 2AFC pipeline, protocol and traceability | Approved, counterbalanced study with participants |
| Autonomous physical prototyping | Firmware template and software guards | Actual assembly, electronics/mechatronics work and measured validation |

The software makes the first columns inspectable. It cannot by itself establish
the practical experience in the final column or determine a selection score.
