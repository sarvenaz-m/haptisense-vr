# Visual and haptic perceptual-acuity protocol

**Status:** design template; no human participants have been recruited.  
**Primary design:** two-alternative forced choice (2AFC), adaptive staircase.  
**Modalities:** visual displacement and haptic intensity/texture discrimination.

## 1. Research questions

1. What is the just-noticeable difference for visual and haptic cues under matched immersive-task conditions?
2. Does congruent force-plus-vibration reduce discrimination threshold relative to force-only or vibration-only feedback?
3. Are threshold estimates associated with device latency, trial order, prior VR experience, or fatigue?

## 2. Hypotheses

- H1: congruent multimodal feedback produces a lower discrimination threshold than either unimodal condition.
- H2: incongruent force–vibration pairing increases response time and error rate.
- H3: thresholds increase across late blocks if fatigue is not controlled.

Confirmatory hypotheses, the primary outcome, sample size, exclusion criteria,
and statistical model should be preregistered before data collection.

## 3. Participants and ethics

- Obtain institutional ethics approval before recruitment.
- Use adult participants capable of giving informed consent.
- Screen for conditions relevant to VR, motion sickness, tactile sensitivity, and device safety.
- Explain that participation is voluntary and withdrawal is possible without penalty.
- Store consent forms separately from pseudonymized trial data.
- Provide an immediate stop control and a researcher-controlled emergency stop.

The target sample size must be justified with an a priori power or precision
analysis based on the chosen primary model. A convenience sample should not be
presented as confirmatory evidence.

## 4. Apparatus and calibration

Record for every session:

- headset and display refresh rate;
- haptic device/actuator model, firmware, and driver;
- measured update rate, end-to-end latency, jitter, and packet loss;
- force and vibration calibration procedure;
- dominant hand, attachment location, and fit;
- software version/commit and configuration hash;
- room, posture, lighting, audio masking, and experimenter.

Run a pre-session safety check with commands capped below the approved limits.
The software safety envelope supplements rather than replaces device-level
watchdogs and physical limits.

## 5. Experimental design

### Conditions

1. Force only.
2. Vibration only.
3. Congruent force plus vibration.
4. Optional incongruent force plus vibration control.

Use a within-participant design when feasible. Counterbalance condition order
with a Latin square or a reproducible randomized schedule.

### Trial

1. Show fixation and neutralize the device.
2. Present reference and comparison intervals in randomized order.
3. Ask which interval contained the stronger, rougher, or larger cue.
4. Record response, correctness, response time, commanded signal, measured signal if available, and safety events.
5. Apply the adaptive rule and continue after a variable inter-trial interval.

### Adaptive rule

The included implementation uses two-down/one-up:

- after two consecutive correct responses, decrease the difference;
- after one error, increase the difference;
- record a reversal when adjustment direction changes;
- estimate the threshold from the final reversal levels.

The exact convergence target, step schedule, number of reversals, and stopping
rule must be fixed before real data collection. Consider decreasing step size
after early reversals for more efficient estimation.

## 6. Outcomes

### Primary

- discrimination threshold estimated from late reversal levels or a fitted psychometric function.

### Secondary

- response time;
- accuracy;
- lapse rate;
- simulator sickness/discomfort score;
- perceived realism and confidence;
- safety-limit events and missing/late packets.

## 7. Quality control and exclusions

Predefine participant- and trial-level rules. Candidate rules include:

- failure to perform above chance in easy catch trials;
- excessive lapse rate;
- incomplete staircase or equipment fault;
- latency or packet loss outside calibrated limits;
- safety stop or participant withdrawal;
- response before stimulus completion;
- duplicated or corrupt record.

Never exclude a participant solely because the result contradicts the
hypothesis. Preserve raw records and log every exclusion with a reason.

## 8. Analysis plan

1. Validate trial integrity and calibration metadata.
2. Plot staircase trajectories and mark reversals.
3. Estimate thresholds with uncertainty intervals.
4. Compare conditions using a preregistered repeated-measures or hierarchical model.
5. Report effect sizes and intervals, not only p-values.
6. Perform sensitivity analysis for predefined exclusion and threshold-estimation choices.
7. Separate confirmatory from exploratory analyses.

If fitting a psychometric function, include guess and lapse parameters suitable
for 2AFC and inspect participant-level fits.

## 9. Data structure

The demonstration CSV contains:

- pseudonymous participant ID;
- modality and trial index;
- reference, comparison, and delta;
- comparison interval and response interval;
- correctness and reversal flag;
- an explicit `synthetic` indicator.

Real datasets should add timestamps, response time, condition, calibration ID,
software commit, device log reference, and exclusion status without storing
direct identifiers in the analysis table.

## 10. Stopping and adverse events

Stop immediately after participant request, pain, numbness, unexpected force,
tracking loss, device instability, severe cybersickness, or experimenter safety
concern. Log the event without pressuring the participant to continue. Follow
the approved institutional reporting procedure.
