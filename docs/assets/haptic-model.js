(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.HaptiSenseModel = api;
})(typeof globalThis !== "undefined" ? globalThis : this, () => {
  "use strict";

  const presets = {
    soft: {
      name: "soft_tissue", stiffness: 650, damping: 7, roughness: 0.38,
      speed: 0.035, friction: 0.18, spatial: 1500, amplitudeGain: 0.82
    },
    fibrous: {
      name: "fibrous_tissue", stiffness: 950, damping: 11, roughness: 0.72,
      speed: 0.042, friction: 0.26, spatial: 2200, amplitudeGain: 0.95
    },
    membrane: {
      name: "smooth_membrane", stiffness: 1200, damping: 5, roughness: 0.16,
      speed: 0.028, friction: 0.12, spatial: 900, amplitudeGain: 0.60
    }
  };

  function clamp(value, lower, upper) {
    return Math.min(upper, Math.max(lower, value));
  }

  function magnitude(vector) {
    return Math.hypot(vector.x, vector.y);
  }

  function clampMagnitude(vector, maximum) {
    const norm = magnitude(vector);
    if (norm <= maximum || norm <= 1e-12) return vector;
    const scale = maximum / norm;
    return { x: vector.x * scale, y: vector.y * scale };
  }

  function mean(values) {
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  function round6(value) {
    return Math.round((value + Number.EPSILON) * 1e6) / 1e6;
  }

  function simulate(options = {}) {
    const presetKey = options.presetKey || "soft";
    const preset = presets[presetKey];
    if (!preset) throw new Error(`Unknown preset: ${presetKey}`);

    const stiffness = Number(options.stiffness ?? preset.stiffness);
    const damping = Number(options.damping ?? preset.damping);
    const roughness = Number(options.roughness ?? preset.roughness);
    const baseSpeed = Number(options.speed ?? preset.speed);
    const sampleRate = Number(options.sampleRate ?? 500);
    const duration = Number(options.duration ?? 4);
    if (!(sampleRate >= 100) || !(duration > 0)) {
      throw new Error("Duration must be positive and sample rate at least 100 Hz");
    }

    const dt = 1 / sampleRate;
    const rows = [];
    let previousForce = { x: 0, y: 0 };
    let filteredInertial = { x: 0, y: 0 };
    let safetyEvents = 0;

    for (let index = 0; index < Math.trunc(sampleRate * duration); index += 1) {
      const t = index * dt;
      const active = t >= 0.45 && t <= duration - 0.30;
      const phase = 2 * Math.PI * 0.62 * Math.max(0, t - 0.45);
      const rawPenetration = active ? 0.0042 + 0.0028 * Math.sin(phase) : 0;
      const penetration = Math.max(0, rawPenetration);
      const penetrationRate = active ? 0.0028 * 2 * Math.PI * 0.62 * Math.cos(phase) : 0;
      const lateralSpeed = active ? baseSpeed + 0.012 * Math.sin(2 * Math.PI * 0.35 * t) : 0;

      const speedIntoSurface = Math.max(0, penetrationRate);
      const normalMagnitude = penetration > 0
        ? Math.max(0, stiffness * penetration + damping * speedIntoSurface)
        : 0;
      const tangentialSpeed = Math.abs(lateralSpeed);
      const frictionScale = Math.min(1, tangentialSpeed / 0.004);
      const frictionMagnitude = preset.friction * normalMagnitude * frictionScale;
      const contact = {
        x: tangentialSpeed <= 1e-12 ? 0 : -Math.sign(lateralSpeed) * frictionMagnitude,
        y: normalMagnitude
      };

      let substrateFree = { x: 0, y: 0 };
      if (active) {
        const acceleration = {
          x: 0.012 * 2 * Math.PI * 0.35 * Math.cos(2 * Math.PI * 0.35 * t),
          y: 0.0028 * Math.pow(2 * Math.PI * 0.62, 2) * Math.sin(phase)
        };
        const target = { x: -0.12 * acceleration.x, y: -0.12 * acceleration.y };
        filteredInertial = clampMagnitude({
          x: filteredInertial.x * 0.78 + target.x * 0.22,
          y: filteredInertial.y * 0.78 + target.y * 0.22
        }, 4);
        substrateFree = filteredInertial;
      }

      const combined = {
        x: contact.x * 0.82 + substrateFree.x * 0.18,
        y: contact.y * 0.82 + substrateFree.y * 0.18
      };
      const rawForceMagnitude = magnitude(combined);
      const contactStrength = clamp(rawForceMagnitude / 4, 0, 1);
      const speedFactor = clamp(tangentialSpeed / 0.08, 0, 1);
      const rawFrequency = rawForceMagnitude <= 1e-12
        ? 20
        : clamp(tangentialSpeed * preset.spatial, 20, 250);
      const rawAmplitude = rawForceMagnitude <= 1e-12
        ? 0
        : clamp(
          roughness * preset.amplitudeGain * (0.2 + 0.8 * contactStrength)
            * (0.15 + 0.85 * speedFactor),
          0,
          1
        );

      const forceClamped = rawForceMagnitude > 6;
      let limitedForce = clampMagnitude(combined, 6);
      const delta = {
        x: limitedForce.x - previousForce.x,
        y: limitedForce.y - previousForce.y
      };
      const maxDelta = 180 * dt;
      const slewClamped = magnitude(delta) > maxDelta;
      const limitedDelta = clampMagnitude(delta, maxDelta);
      limitedForce = {
        x: previousForce.x + limitedDelta.x,
        y: previousForce.y + limitedDelta.y
      };
      previousForce = limitedForce;

      const amplitude = clamp(rawAmplitude, 0, 0.85);
      const frequency = clamp(rawFrequency, 20, 250);
      if (forceClamped || slewClamped || amplitude !== rawAmplitude || frequency !== rawFrequency) {
        safetyEvents += 1;
      }

      rows.push({
        t,
        force: magnitude(limitedForce),
        vibration: amplitude,
        frequency,
        penetration,
        contactForce: magnitude(contact),
        inertialForce: magnitude(substrateFree),
        contactStrength
      });
    }

    const forces = rows.map((row) => row.force);
    const vibrations = rows.map((row) => row.vibration);
    return {
      rows,
      metrics: {
        samples: rows.length,
        sampleRate,
        peak: round6(Math.max(...forces)),
        rms: round6(Math.sqrt(mean(forces.map((value) => value * value)))),
        meanVibration: round6(mean(vibrations)),
        safetyEvents
      }
    };
  }

  return { presets, simulate };
});
