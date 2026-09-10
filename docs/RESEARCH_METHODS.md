# Contact mechanics studio · v0.3

This workbench studies **computational contact response**. Every displayed force
is calculated; none is a measured actuator output. The workbench runs locally
with no account, external assets or participant-data collection.

## Three explicit contact laws

Penetration `d` is positive into the surface [m]; `v = ḋ` is approach velocity
[m/s]. The surface normal points outwards. Equilibrium force is

```math
F_e = k(d + \beta d^3).
```

`k` is in N/m and `β` in m⁻². The default `β = 12000` is an illustrative
nonlinear correction. This is a lumped contact law, not a modulus or a tissue fit.

| Model | Raw normal force while in contact | Memory |
|---|---|---|
| Elastic | `max(0, F_e)` | None |
| Kelvin–Voigt variant | `max(0, F_e + c max(v, 0))` | Approach-only damping |
| SLS branch | `max(0, F_e + q)` | Maxwell branch in parallel with equilibrium elasticity |

For the SLS branch, `k_m = relaxation × k`, and

```math
\dot q + q/\tau = k_m v,\qquad
q_{n+1}=a q_n + k_m\tau(1-a)v_n,\quad a=e^{-\Delta t/\tau}.
```

This update is exact **within a step with constant input velocity**. Sampling a
smooth trajectory still introduces discretization error. With `β=0`, the
elastic-plus-Maxwell structure is the standard linear solid; with `β>0` the
equilibrium spring is nonlinear. A stationary hold gives exponential decay of
`q` toward zero. Contact loss clears memory and commands; this simplifying
reset does not model detached-material recovery or adhesion.

The spring/dashpot background follows the mechanical analogues discussed in
[David Roylance, Engineering Viscoelasticity, MIT](https://web.mit.edu/course/3/3.11/www/modules/visco.pdf).
The unilateral contact, cubic spring and cue mapping are project design choices.

## Tangential and cutaneous channels

```math
F_t=-\mu F_n\tanh(v_x/0.004).
```

Thus `F_t v_x ≤ 0` for the raw friction channel. Amplitude depends on roughness,
normal load and lateral speed; frequency is `|v_x| × spatial_frequency`, bounded
to 20–250 Hz when amplitude is nonzero. Amplitude is dimensionless, capped at
0.85. Zero scan speed produces zero vibration amplitude. The displayed waveform
is a command illustration, not a vibration recording.

## Command limits and energy diagnostics

The raw `(F_t, F_n)` vector is magnitude-limited (default 6 N), then
slew-limited (default 180 N/s). No-contact and invalid-input resets take precedence
over the slew bound and clear state. Parameters and inputs reject nonfinite and
out-of-envelope values. These are computational guards, not certified hardware
safety or a passivity controller.

Command power is `P = Fx vx − Fy v`. Positive and negative work are sums of the
corresponding power samples multiplied by `Δt`. Positive work can reflect
stored-energy return. Neither its presence nor absence proves closed-loop
stability; no user/device dynamics or transport delays are included.

## Controlled experiments

The default four-second protocol has smooth approach, stationary hold and
release. A second protocol runs two smooth loading cycles. The comparison tab
uses the **same trajectory, time step and shared parameters** for all three
laws. Presets alter several parameters; comparing presets alone cannot isolate
the effect of one parameter. To inspect stiffness alone, vary its slider with
all other settings fixed.

The default rate is 500 **model samples per second**. The browser replays a
precomputed trace at display frame rate. Neither rendering nor offline batch
timing establishes a 500 Hz physical servo. The default trace contains 2,001
samples including both endpoints; the v0.2 trace convention is unchanged.

## Parameter identification

[`identification.py`](../src/haptisense/identification.py) estimates `k` and `c`
for the **linear** approach-damped Kelvin model (`β=0`) from in-contact rows
with `depth_m`, `velocity_m_s`, `normal_n`. It solves the two-parameter normal
equations, rejects nearly collinear experimental designs and unphysical fits,
and reports held-out RMSE and maximum absolute error. Input force must be raw
normal force, not command magnitude after limiting.

The committed self-check varies depth and speed independently, fits nine
synthetic training points and evaluates four distinct held-out points. Near-zero
error on noiseless data validates the estimator implementation only. Actual
identification needs calibrated measurements, uncertainty characterization,
model-mismatch analysis and a genuinely independent validation set.

## Visual and integration scope

The browser surface uses camera-projected geometry drawn with Canvas 2D. Its
Gaussian indentation is illustrative; it does not solve continuum mechanics.
The tool shows indentation at a fixed visual location while scan speed affects
friction and cues; it does not animate the full tangential path. Decorative
strata are not separate constitutive layers. Orbit with mouse/touch or arrow
keys. All important numerical outputs also exist in HTML and CSV.

The desktop Unity builder and UDP scripts are **source-level integration work**.
Unity Editor execution, a tracked headset, PHANTOM/Geomagic integration, AVR
deployment and physical force validation are not evidenced by browser tests.
Optional firmware remains unflashed reference material.

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m haptisense research --output results/my-contact-run --model sls --protocol hold
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/workbench.html`. Export JSON to preserve parameters,
protocol, version, evidence label and every sample. CSV exports the numerical
trace. Import accepts computational v0.3 sessions and **recomputes** results from
validated parameters; supplied rows are never trusted. Output directories must
be new so earlier CLI evidence is not overwritten.

See [validation](VALIDATION_V03.md), [provenance](../PROVENANCE.md),
[the perceptual protocol](EXPERIMENT_PROTOCOL.md) and [the reviewer tour](REVIEWER_TOUR.md).
