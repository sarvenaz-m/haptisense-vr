/* SI-unit contact model; no browser, device, or rendering dependency. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.HaptiSenseResearch = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  'use strict';
  const defaults = Object.freeze({
    model: 'sls',
    stiffness: 650,
    damping: 7,
    relaxation: 0.65,
    tau: 0.25,
    nonlinear: 12000,
    friction: 0.18,
    roughness: 0.38,
    spatial: 1500,
    depth: 0.006,
    speed: 0.035,
    rate: 500,
    duration: 4,
    force_limit: 6,
    slew_limit: 180
  });
  const bounds = {
    stiffness: [1, 5000],
    damping: [0, 100],
    relaxation: [0, 4],
    tau: [0.01, 5],
    nonlinear: [0, 100000],
    friction: [0, 1],
    roughness: [0, 1],
    spatial: [100, 5000],
    depth: [0.0001, 0.012],
    speed: [0, 0.15],
    rate: [100, 2000],
    duration: [1, 12],
    force_limit: [0.1, 12],
    slew_limit: [1, 1000]
  };

  function config(options = {}) {
    for (const key of Object.keys(options))
      if (!(key in defaults)) throw Error(`Unknown parameter: ${key}`);
    const c = {
      ...defaults,
      ...options
    };
    if (!['elastic', 'kelvin', 'sls'].includes(c.model)) throw Error('Unknown contact model');
    for (const [key, [low, high]] of Object.entries(bounds)) {
      if (typeof c[key] !== 'number' || !Number.isFinite(c[key]) || c[key] < low || c[key] > high)
        throw Error(`${key} must be finite in [${low}, ${high}]`);
    }
    if (!Number.isInteger(c.rate)) throw Error('rate must be an integer');
    return c;
  }

  function trajectory(t, c, protocol = 'hold') {
    const u = t / c.duration;
    let f = 0,
      v = 0;
    if (protocol === 'hold') {
      if (u >= 0.1 && u < 0.3) {
        const p = (u - 0.1) / 0.2;
        f = (1 - Math.cos(Math.PI * p)) / 2;
        v = Math.PI * Math.sin(Math.PI * p) / (0.4 * c.duration);
      } else if (u >= 0.3 && u <= 0.65) f = 1;
      else if (u > 0.65 && u < 0.9) {
        const p = (u - 0.65) / 0.25;
        f = (1 + Math.cos(Math.PI * p)) / 2;
        v = -Math.PI * Math.sin(Math.PI * p) / (0.5 * c.duration);
      }
    } else if (protocol === 'cycle') {
      if (u >= 0.1 && u < 0.9) {
        const p = (u - 0.1) / 0.8;
        f = Math.sin(2 * Math.PI * p) ** 2;
        v = 2 * Math.PI * Math.sin(4 * Math.PI * p) / (0.8 * c.duration);
      }
    } else throw Error('Unknown trajectory');
    return [c.depth * f, c.depth * v, c.speed * t];
  }
  class Contact {
    constructor(options = {}) {
      this.c = config(options);
      this.memory = 0;
      this.previous = [0, 0];
    }
    step(depth, velocity, lateral) {
      const c = this.c,
        dt = 1 / c.rate;
      if (![depth, velocity, lateral].every(Number.isFinite) || depth < 0 || depth > 0.02 || Math.abs(velocity) > 1 || Math.abs(lateral) > 1) {
        this.memory = 0;
        this.previous = [0, 0];
        throw Error('Contact input outside computational envelope');
      }
      let elastic = c.stiffness * (depth + c.nonlinear * depth ** 3),
        viscous = c.model === 'kelvin' ? c.damping * Math.max(0, velocity) : 0;
      let normal = 0,
        friction = 0,
        fx = 0,
        fy = 0,
        amplitude = 0,
        frequency = 0,
        limited = false;
      if (depth <= 1e-12) {
        this.memory = 0;
        this.previous = [0, 0];
        elastic = viscous = 0;
      } else {
        const a = Math.exp(-dt / c.tau);
        this.memory = c.model === 'sls' ? a * this.memory + c.stiffness * c.relaxation * c.tau * (1 - a) * velocity : 0;
        normal = Math.max(0, elastic + viscous + this.memory);
        friction = -c.friction * normal * Math.tanh(lateral / 0.004);
        const norm = Math.hypot(friction, normal),
          scale = Math.min(1, c.force_limit / Math.max(norm, 1e-12));
        const delta = [friction * scale - this.previous[0], normal * scale - this.previous[1]];
        const slew = Math.min(1, c.slew_limit * dt / Math.max(Math.hypot(...delta), 1e-12));
        [fx, fy] = this.previous.map((p, i) => p + delta[i] * slew);
        this.previous = [fx, fy];
        limited = scale < 1 || slew < 1;
        amplitude = Math.min(0.85, c.roughness * Math.min(1, normal / 4) * Math.min(1, Math.abs(lateral) / 0.08));
        frequency = amplitude > 0 ? Math.min(250, Math.max(20, Math.abs(lateral) * c.spatial)) : 0;
      }
      return {
        elastic_n: elastic,
        viscous_n: viscous,
        memory_n: this.memory,
        normal_n: normal,
        friction_n: friction,
        fx_n: fx,
        fy_n: fy,
        command_n: Math.hypot(fx, fy),
        amplitude,
        frequency_hz: frequency,
        limited,
        power_w: fx * lateral - fy * velocity
      };
    }
  }

  function simulate(options = {}, protocol = 'hold') {
    const c = config(options),
      model = new Contact(c),
      rows = [];
    if (!['hold', 'cycle'].includes(protocol)) throw Error('Unknown trajectory');
    let sumSq = 0,
      peak = 0,
      limited = 0,
      pos = 0,
      neg = 0;
    for (let i = 0; i <= Math.trunc(c.rate * c.duration); i++) {
      const t = i / c.rate,
        [d, v, x] = trajectory(t, c, protocol),
        r = {
          t_s: t,
          depth_m: d,
          velocity_m_s: v,
          x_m: x,
          ...model.step(d, v, c.speed)
        };
      rows.push(r);
      sumSq += r.command_n ** 2;
      peak = Math.max(peak, r.command_n);
      limited += Number(r.limited);
      pos += Math.max(0, r.power_w) / c.rate;
      neg += Math.min(0, r.power_w) / c.rate;
    }
    return {
      schema: 'haptisense.research.v1',
      version: '0.3.0',
      evidence: 'synthetic_computational',
      config: c,
      protocol,
      metrics: {
        samples: rows.length,
        peak_command_n: peak,
        rms_command_n: Math.sqrt(sumSq / rows.length),
        limited_samples: limited,
        positive_command_work_j: pos,
        negative_command_work_j: neg
      },
      rows
    };
  }

  function csv(session) {
    const keys = Object.keys(session.rows[0]);
    return keys.join(',') + '\n' + session.rows.map(r => keys.map(k => typeof r[k] === 'boolean' ? Number(r[k]) : r[k]).join(',')).join('\n') + '\n';
  }

  function restore(text) {
    if (text.length > 8000000) throw Error('Session exceeds 8 MB');
    const data = JSON.parse(text);
    if (data.schema !== 'haptisense.research.v1' || data.version !== '0.3.0' || data.evidence !== 'synthetic_computational')
      throw Error('Expected a v0.3 computational research session');
    // Recompute from validated parameters; imported results are never trusted.
    return simulate(data.config, data.protocol);
  }
  return {
    defaults,
    config,
    Contact,
    trajectory,
    simulate,
    csv,
    restore
  };
});
