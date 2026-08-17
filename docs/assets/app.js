(() => {
  "use strict";

  const presets = {
    soft: { stiffness: 650, damping: 7, roughness: 0.38, speed: 0.035, friction: 0.18, spatial: 1500 },
    fibrous: { stiffness: 950, damping: 11, roughness: 0.72, speed: 0.042, friction: 0.26, spatial: 2200 },
    membrane: { stiffness: 1200, damping: 5, roughness: 0.16, speed: 0.028, friction: 0.12, spatial: 900 }
  };

  let currentPreset = "soft";
  const $ = (id) => document.getElementById(id);
  const controls = {
    stiffness: $("stiffness"),
    damping: $("damping"),
    roughness: $("roughness"),
    speed: $("speed")
  };

  function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }

  function updateLabels() {
    $("stiffness-out").value = `${Number(controls.stiffness.value).toFixed(0)} N/m`;
    $("damping-out").value = `${Number(controls.damping.value).toFixed(1)} Ns/m`;
    $("roughness-out").value = Number(controls.roughness.value).toFixed(2);
    $("speed-out").value = `${Number(controls.speed.value).toFixed(3)} m/s`;
  }

  function simulate() {
    const p = presets[currentPreset];
    const stiffness = Number(controls.stiffness.value);
    const damping = Number(controls.damping.value);
    const roughness = Number(controls.roughness.value);
    const baseSpeed = Number(controls.speed.value);
    const rate = 180;
    const duration = 4;
    const dt = 1 / rate;
    const rows = [];
    let previousForce = 0;
    let filteredInertial = 0;
    let safetyEvents = 0;

    for (let index = 0; index < rate * duration; index += 1) {
      const t = index * dt;
      const active = t >= 0.45 && t <= duration - 0.30;
      const phase = 2 * Math.PI * 0.62 * Math.max(0, t - 0.45);
      const penetration = active ? Math.max(0, 0.0042 + 0.0028 * Math.sin(phase)) : 0;
      const penetrationRate = active ? 0.0028 * 2 * Math.PI * 0.62 * Math.cos(phase) : 0;
      const lateralSpeed = active ? baseSpeed + 0.012 * Math.sin(2 * Math.PI * 0.35 * t) : 0;
      const speedInto = Math.max(0, penetrationRate);
      const normalForce = penetration > 0 ? stiffness * penetration + damping * speedInto : 0;
      const frictionScale = Math.min(1, Math.abs(lateralSpeed) / 0.004);
      const frictionForce = p.friction * normalForce * frictionScale;
      const contactForce = Math.sqrt(normalForce * normalForce + frictionForce * frictionForce);
      const accel = active ? 0.0028 * Math.pow(2 * Math.PI * 0.62, 2) * Math.sin(phase) : 0;
      const inertialTarget = Math.abs(0.12 * accel);
      filteredInertial = filteredInertial * 0.78 + inertialTarget * 0.22;
      const rawForce = 0.82 * contactForce + 0.18 * filteredInertial;

      const forceCapped = Math.min(6, rawForce);
      const maxDelta = 180 * dt;
      const delta = clamp(forceCapped - previousForce, -maxDelta, maxDelta);
      const safeForce = previousForce + delta;
      if (Math.abs(forceCapped - previousForce) > maxDelta || rawForce > 6) safetyEvents += 1;
      previousForce = safeForce;

      const contactStrength = clamp(rawForce / 4, 0, 1);
      const speedFactor = clamp(Math.abs(lateralSpeed) / 0.08, 0, 1);
      const frequency = clamp(Math.abs(lateralSpeed) * p.spatial, 20, 250);
      const vibration = rawForce > 0
        ? clamp(roughness * 0.82 * (0.2 + 0.8 * contactStrength) * (0.15 + 0.85 * speedFactor), 0, 0.85)
        : 0;
      rows.push({ t, force: safeForce, vibration, frequency, penetration });
    }
    return { rows, safetyEvents };
  }

  function drawAxes(context, width, height, padding) {
    context.clearRect(0, 0, width, height);
    context.fillStyle = "#fbfdfd";
    context.fillRect(0, 0, width, height);
    context.strokeStyle = "#e5eded";
    context.lineWidth = 1;
    context.font = "11px ui-sans-serif, system-ui";
    context.fillStyle = "#7b8e9b";
    for (let i = 0; i <= 4; i += 1) {
      const y = padding.top + ((height - padding.top - padding.bottom) * i) / 4;
      context.beginPath(); context.moveTo(padding.left, y); context.lineTo(width - padding.right, y); context.stroke();
      context.fillText((1 - i / 4).toFixed(2), 12, y + 4);
    }
    for (let i = 0; i <= 4; i += 1) {
      const x = padding.left + ((width - padding.left - padding.right) * i) / 4;
      context.fillText(`${i}s`, x - 7, height - 12);
    }
  }

  function drawHapticChart(rows) {
    const canvas = $("haptic-chart");
    const context = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const pad = { left: 55, right: 22, top: 24, bottom: 38 };
    drawAxes(context, width, height, pad);
    const maxForce = Math.max(...rows.map((row) => row.force), 1);
    const x = (index) => pad.left + (index / (rows.length - 1)) * (width - pad.left - pad.right);
    const y = (value) => pad.top + (1 - value) * (height - pad.top - pad.bottom);

    const gradient = context.createLinearGradient(0, pad.top, 0, height - pad.bottom);
    gradient.addColorStop(0, "rgba(0,166,166,.22)");
    gradient.addColorStop(1, "rgba(0,166,166,0)");
    context.beginPath();
    rows.forEach((row, index) => {
      const px = x(index); const py = y(row.force / (maxForce * 1.05));
      if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
    });
    context.lineTo(x(rows.length - 1), height - pad.bottom); context.lineTo(x(0), height - pad.bottom); context.closePath();
    context.fillStyle = gradient; context.fill();

    const plot = (key, scale, color, lineWidth) => {
      context.beginPath();
      rows.forEach((row, index) => {
        const px = x(index); const py = y(row[key] / scale);
        if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
      });
      context.strokeStyle = color; context.lineWidth = lineWidth; context.lineJoin = "round"; context.stroke();
    };
    plot("force", maxForce * 1.05, "#00a6a6", 3.4);
    plot("vibration", 1, "#f17463", 2.5);
  }

  function mulberry32(seed) {
    return () => {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let value = Math.imul(seed ^ seed >>> 15, 1 | seed);
      value = value + Math.imul(value ^ value >>> 7, 61 | value) ^ value;
      return ((value ^ value >>> 14) >>> 0) / 4294967296;
    };
  }

  function staircaseData(threshold, seed) {
    const random = mulberry32(seed);
    let delta = 0.2; let streak = 0;
    const values = [];
    for (let trial = 0; trial < 72; trial += 1) {
      values.push(delta);
      const probability = 0.5 + 0.5 / (1 + Math.exp(-(delta - threshold) / 0.018));
      const correct = random() < Math.min(0.985, probability);
      if (correct) {
        streak += 1;
        if (streak >= 2) { delta = Math.max(0.005, delta - 0.025); streak = 0; }
      } else { delta = Math.min(0.4, delta + 0.025); streak = 0; }
    }
    return values;
  }

  function drawStaircase() {
    const canvas = $("staircase-chart");
    const context = canvas.getContext("2d");
    const width = canvas.width; const height = canvas.height;
    const pad = { left: 48, right: 18, top: 20, bottom: 36 };
    drawAxes(context, width, height, pad);
    const visual = staircaseData(0.04, 255);
    const haptic = staircaseData(0.0675, 945);
    const plot = (values, color) => {
      context.beginPath();
      values.forEach((value, index) => {
        const px = pad.left + index / (values.length - 1) * (width - pad.left - pad.right);
        const py = pad.top + (1 - value / 0.25) * (height - pad.top - pad.bottom);
        if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
      });
      context.strokeStyle = color; context.lineWidth = 2.5; context.lineJoin = "round"; context.stroke();
    };
    plot(visual, "#00a6a6"); plot(haptic, "#f17463");
    context.fillStyle = "#607787"; context.font = "11px ui-sans-serif, system-ui";
    context.fillText("visual", width - 112, 22); context.fillStyle = "#00a6a6"; context.fillRect(width - 136, 16, 17, 2);
    context.fillStyle = "#607787"; context.fillText("haptic", width - 49, 22); context.fillStyle = "#f17463"; context.fillRect(width - 75, 16, 17, 2);
  }

  function render() {
    updateLabels();
    const simulation = simulate();
    drawHapticChart(simulation.rows);
    const forces = simulation.rows.map((row) => row.force);
    const vibrations = simulation.rows.map((row) => row.vibration);
    const peak = Math.max(...forces);
    const rms = Math.sqrt(forces.reduce((sum, value) => sum + value * value, 0) / forces.length);
    const meanVibration = vibrations.reduce((sum, value) => sum + value, 0) / vibrations.length;
    $("peak-force").textContent = peak.toFixed(3);
    $("rms-force").textContent = rms.toFixed(3);
    $("mean-vibration").textContent = meanVibration.toFixed(3);
    $("safety-events").textContent = simulation.safetyEvents;
    $("hero-force").textContent = `${peak.toFixed(2)} N`;
    const activeFrequencies = simulation.rows.filter((row) => row.vibration > 0).map((row) => row.frequency);
    const meanFrequency = activeFrequencies.reduce((sum, value) => sum + value, 0) / Math.max(activeFrequencies.length, 1);
    $("hero-vibro").textContent = `${meanFrequency.toFixed(1)} Hz`;
  }

  document.querySelectorAll(".preset").forEach((button) => {
    button.addEventListener("click", () => {
      currentPreset = button.dataset.preset;
      document.querySelectorAll(".preset").forEach((item) => item.classList.toggle("active", item === button));
      const p = presets[currentPreset];
      Object.entries({ stiffness: p.stiffness, damping: p.damping, roughness: p.roughness, speed: p.speed })
        .forEach(([key, value]) => { controls[key].value = value; });
      render();
    });
  });
  Object.values(controls).forEach((control) => control.addEventListener("input", render));
  $("reset-controls").addEventListener("click", () => document.querySelector(`.preset[data-preset="${currentPreset}"]`).click());
  drawStaircase();
  render();
})();
