(() => {
  "use strict";

  const model = window.HaptiSenseModel;
  const psychophysics = window.HaptiSensePsychophysics;
  if (!model || !psychophysics) {
    throw new Error("HaptiSense model assets failed to load");
  }

  let currentPreset = "soft";
  const $ = (id) => document.getElementById(id);
  const controls = {
    stiffness: $("stiffness"),
    damping: $("damping"),
    roughness: $("roughness"),
    speed: $("speed")
  };

  function updateLabels() {
    $("stiffness-out").value = `${Number(controls.stiffness.value).toFixed(0)} N/m`;
    $("damping-out").value = `${Number(controls.damping.value).toFixed(1)} Ns/m`;
    $("roughness-out").value = Number(controls.roughness.value).toFixed(2);
    $("speed-out").value = `${Number(controls.speed.value).toFixed(3)} m/s`;
  }

  function drawAxes(context, width, height, padding, xLabels = true) {
    context.clearRect(0, 0, width, height);
    context.fillStyle = "#fbfdfd";
    context.fillRect(0, 0, width, height);
    context.strokeStyle = "#e5eded";
    context.lineWidth = 1;
    context.font = "11px ui-sans-serif, system-ui";
    context.fillStyle = "#7b8e9b";
    for (let index = 0; index <= 4; index += 1) {
      const y = padding.top + ((height - padding.top - padding.bottom) * index) / 4;
      context.beginPath();
      context.moveTo(padding.left, y);
      context.lineTo(width - padding.right, y);
      context.stroke();
      context.fillText((1 - index / 4).toFixed(2), 12, y + 4);
    }
    if (xLabels) {
      for (let index = 0; index <= 4; index += 1) {
        const x = padding.left + ((width - padding.left - padding.right) * index) / 4;
        context.fillText(`${index}s`, x - 7, height - 12);
      }
    }
  }

  function drawHapticChart(rows) {
    const canvas = $("haptic-chart");
    const context = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const padding = { left: 55, right: 22, top: 24, bottom: 38 };
    drawAxes(context, width, height, padding);
    const maxForce = Math.max(...rows.map((row) => row.force), 1);
    const x = (index) => padding.left + (index / (rows.length - 1))
      * (width - padding.left - padding.right);
    const y = (value) => padding.top + (1 - value) * (height - padding.top - padding.bottom);

    const gradient = context.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, "rgba(0,166,166,.22)");
    gradient.addColorStop(1, "rgba(0,166,166,0)");
    context.beginPath();
    rows.forEach((row, index) => {
      const px = x(index);
      const py = y(row.force / (maxForce * 1.05));
      if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
    });
    context.lineTo(x(rows.length - 1), height - padding.bottom);
    context.lineTo(x(0), height - padding.bottom);
    context.closePath();
    context.fillStyle = gradient;
    context.fill();

    const plot = (key, scale, color, lineWidth) => {
      context.beginPath();
      rows.forEach((row, index) => {
        const px = x(index);
        const py = y(row[key] / scale);
        if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
      });
      context.strokeStyle = color;
      context.lineWidth = lineWidth;
      context.lineJoin = "round";
      context.stroke();
    };
    plot("force", maxForce * 1.05, "#00a6a6", 3.4);
    plot("vibration", 1, "#f17463", 2.5);

    context.save();
    context.translate(15, height / 2 + 56);
    context.rotate(-Math.PI / 2);
    context.fillStyle = "#7b8e9b";
    context.font = "11px ui-sans-serif, system-ui";
    context.fillText("Normalised display scale", 0, 0);
    context.restore();
  }

  function drawStaircase() {
    const canvas = $("staircase-chart");
    const context = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const padding = { left: 48, right: 18, top: 20, bottom: 36 };
    drawAxes(context, width, height, padding, false);
    const plot = (values, color) => {
      context.beginPath();
      values.forEach((value, index) => {
        const px = padding.left + index / (values.length - 1) * (width - padding.left - padding.right);
        const py = padding.top + (1 - value / 0.25) * (height - padding.top - padding.bottom);
        if (index === 0) context.moveTo(px, py); else context.lineTo(px, py);
      });
      context.strokeStyle = color;
      context.lineWidth = 2.5;
      context.lineJoin = "round";
      context.stroke();
    };
    plot(psychophysics.visual, "#00a6a6");
    plot(psychophysics.haptic, "#f17463");
    context.fillStyle = "#607787";
    context.font = "11px ui-sans-serif, system-ui";
    context.fillText("visual", width - 112, 22);
    context.fillStyle = "#00a6a6";
    context.fillRect(width - 136, 16, 17, 2);
    context.fillStyle = "#607787";
    context.fillText("haptic", width - 49, 22);
    context.fillStyle = "#f17463";
    context.fillRect(width - 75, 16, 17, 2);
    context.fillStyle = "#7b8e9b";
    for (let index = 0; index <= 3; index += 1) {
      const x = padding.left + index / 3 * (width - padding.left - padding.right);
      context.fillText(String(index * 24), x - 5, height - 12);
    }
  }

  function render() {
    updateLabels();
    const simulation = model.simulate({
      presetKey: currentPreset,
      stiffness: Number(controls.stiffness.value),
      damping: Number(controls.damping.value),
      roughness: Number(controls.roughness.value),
      speed: Number(controls.speed.value),
      sampleRate: 500,
      duration: 4
    });
    drawHapticChart(simulation.rows);
    const metrics = simulation.metrics;
    $("peak-force").textContent = metrics.peak.toFixed(3);
    $("rms-force").textContent = metrics.rms.toFixed(3);
    $("mean-vibration").textContent = metrics.meanVibration.toFixed(3);
    $("safety-events").textContent = metrics.safetyEvents;
    $("hero-force").textContent = `${metrics.peak.toFixed(2)} N`;
    const activeFrequencies = simulation.rows
      .filter((row) => row.vibration > 0)
      .map((row) => row.frequency);
    const meanFrequency = activeFrequencies.reduce((sum, value) => sum + value, 0)
      / Math.max(activeFrequencies.length, 1);
    $("hero-vibro").textContent = `${meanFrequency.toFixed(1)} Hz`;
  }

  document.querySelectorAll(".preset").forEach((button) => {
    button.addEventListener("click", () => {
      currentPreset = button.dataset.preset;
      document.querySelectorAll(".preset").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      const preset = model.presets[currentPreset];
      Object.entries({
        stiffness: preset.stiffness,
        damping: preset.damping,
        roughness: preset.roughness,
        speed: preset.speed
      }).forEach(([key, value]) => { controls[key].value = value; });
      render();
    });
  });
  Object.values(controls).forEach((control) => control.addEventListener("input", render));
  $("reset-controls").addEventListener("click", () => {
    document.querySelector(`.preset[data-preset="${currentPreset}"]`).click();
  });
  drawStaircase();
  render();
})();
