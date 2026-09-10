/* Camera projection and scientific plots. Geometry is illustrative, not FEM. */
(function(root) {
  'use strict';

  function context(canvas) {
    const box = canvas.getBoundingClientRect(),
      ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, box.width),
      height = Math.max(1, box.height);
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
    }
    const ctx = canvas.getContext('2d');
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    return {
      ctx,
      width,
      height
    };
  }
  class SurfaceView {
    constructor(canvas, onChange) {
      this.canvas = canvas;
      this.azimuth = -0.55;
      this.elevation = 0.66;
      this.onChange = onChange;
      this.drag = null;
      canvas.addEventListener('pointerdown', e => {
        this.drag = {
          x: e.clientX,
          y: e.clientY
        };
        canvas.setPointerCapture(e.pointerId);
      });
      canvas.addEventListener('pointermove', e => {
        if (!this.drag) return;
        this.azimuth += (e.clientX - this.drag.x) * 0.008;
        this.elevation = Math.max(0.22, Math.min(1.25, this.elevation + (e.clientY - this.drag.y) * 0.006));
        this.drag = {
          x: e.clientX,
          y: e.clientY
        };
        this.onChange();
      });
      const stop = () => {
        this.drag = null;
      };
      canvas.addEventListener('pointerup', stop);
      canvas.addEventListener('pointercancel', stop);
      canvas.addEventListener('keydown', e => {
        if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
          e.preventDefault();
          this.azimuth += e.key === 'ArrowLeft' ? -0.12 : 0.12;
          this.onChange();
        }
      });
    }
    reset() {
      this.azimuth = -0.55;
      this.elevation = 0.66;
      this.onChange();
    }
    draw(row) {
      const {
        ctx: c,
        width: w,
        height: h
      } = context(this.canvas), scale = Math.min(w / 115, h / 86);
      const ca = Math.cos(this.azimuth),
        sa = Math.sin(this.azimuth),
        ce = Math.cos(this.elevation),
        se = Math.sin(this.elevation);
      const project = (x, y, z) => {
        const rx = x * ca - z * sa,
          rz = x * sa + z * ca;
        return {
          x: w / 2 + rx * scale,
          y: h * .61 - (y * ce - rz * se) * scale,
          z: rz * ce + y * se
        };
      };
      const path = (points, fill, stroke, width = 1) => {
        c.beginPath();
        points.forEach((p, i) => i ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y));
        c.closePath();
        if (fill) {
          c.fillStyle = fill;
          c.fill();
        }
        if (stroke) {
          c.strokeStyle = stroke;
          c.lineWidth = width;
          c.stroke();
        }
      };
      const line = (a, b, color, width = 1) => {
        c.beginPath();
        c.moveTo(a.x, a.y);
        c.lineTo(b.x, b.y);
        c.strokeStyle = color;
        c.lineWidth = width;
        c.stroke();
      };
      // Ground plane and understated metric grid.
      for (let x = -50; x <= 50; x += 10) line(project(x, -20, -35), project(x, -20, 35), '#32485155');
      for (let z = -30; z <= 30; z += 10) line(project(-50, -20, z), project(50, -20, z), '#32485155');
      const corners = [
        [-40, -16, -28],
        [40, -16, -28],
        [40, -16, 28],
        [-40, -16, 28]
      ].map(p => project(...p));
      path(corners, '#0b1a21', '#466771');
      for (const side of [
          [-40, -28, 40, -28],
          [40, -28, 40, 28],
          [40, 28, -40, 28],
          [-40, 28, -40, -28]
        ]) {
        const [x1, z1, x2, z2] = side;
        path([project(x1, 0, z1), project(x2, 0, z2), project(x2, -16, z2), project(x1, -16, z1)], '#23423f65', '#638c7950');
        line(project(x1, -5, z1), project(x2, -5, z2), '#bdac6944');
        line(project(x1, -10, z1), project(x2, -10, z2), '#b89ae244');
      }
      const depth = row.depth_m * 1000,
        cells = [];
      const surface = (x, z) => -depth * Math.exp(-(x * x + z * z) / 180);
      for (let i = 0; i < 32; i++)
        for (let j = 0; j < 22; j++) {
          const x = -40 + i * 2.5,
            z = -28 + j * 56 / 22;
          const coords = [
            [x, z],
            [x + 2.5, z],
            [x + 2.5, z + 56 / 22],
            [x, z + 56 / 22]
          ];
          const points = coords.map(([a, b]) => project(a, surface(a, b), b));
          const contact = Math.exp(-((x + 1.25) ** 2 + (z + 1.2) ** 2) / 220) * Math.min(1, depth / 6);
          cells.push({
            points,
            z: points.reduce((s, p) => s + p.z, 0) / 4,
            contact
          });
        }
      cells.sort((a, b) => a.z - b.z);
      for (const cell of cells) {
        const t = cell.contact;
        path(cell.points, `rgb(${Math.round(26+t*86)},${Math.round(91+t*85)},${Math.round(84+t*52)})`, '#89eaca35', 0.65);
      }
      // Contact ring and metallic probe are visual encodings of penetration.
      const ring = [];
      for (let i = 0; i < 80; i++) {
        const a = i / 80 * Math.PI * 2,
          x = Math.cos(a) * 9,
          z = Math.sin(a) * 9;
        ring.push(project(x, surface(x, z) + .12, z));
      }
      path(ring, null, '#9cedd477', 1);
      const tip = project(0, -depth + 1.6, 0),
        top = project(0, 33 - depth, 0),
        radius = 3.2 * scale;
      c.save();
      c.shadowColor = '#0008';
      c.shadowBlur = 14;
      const metal = c.createLinearGradient(tip.x - radius, 0, tip.x + radius, 0);
      metal.addColorStop(0, '#475963');
      metal.addColorStop(.35, '#e6eff0');
      metal.addColorStop(.6, '#94a8b4');
      metal.addColorStop(1, '#374952');
      c.strokeStyle = metal;
      c.lineWidth = radius * 2;
      c.lineCap = 'round';
      c.beginPath();
      c.moveTo(top.x, top.y);
      c.lineTo(tip.x, tip.y);
      c.stroke();
      c.restore();
      line(project(0, 24 - depth, 0), project(0, 16 - depth, 0), '#344b56', radius * 2.3);
      const tipGlow = c.createRadialGradient(tip.x - 2, tip.y - 2, 1, tip.x, tip.y, radius * 1.4);
      tipGlow.addColorStop(0, '#fff8d5');
      tipGlow.addColorStop(.45, '#e3c890');
      tipGlow.addColorStop(1, '#577b70');
      c.beginPath();
      c.ellipse(tip.x, tip.y, radius, radius * .68, 0, 0, Math.PI * 2);
      c.fillStyle = tipGlow;
      c.fill();
      const arrow = (a, b, color, label) => {
        line(a, b, color, 1.8);
        const angle = Math.atan2(b.y - a.y, b.x - a.x);
        path([b, {
          x: b.x - 8 * Math.cos(angle - .4),
          y: b.y - 8 * Math.sin(angle - .4)
        }, {
          x: b.x - 8 * Math.cos(angle + .4),
          y: b.y - 8 * Math.sin(angle + .4)
        }], color);
        c.font = '10px monospace';
        c.fillStyle = color;
        c.fillText(label, b.x + 9, b.y - 3);
      };
      if (row.normal_n > .02) {
        arrow(project(7, -depth, 0), project(7, Math.min(26, row.normal_n * 4) - depth, 0), '#ecc587', 'Fn');
        arrow(project(0, 2 - depth, 3), project(-Math.min(20, Math.abs(row.friction_n) * 13), 2 - depth, 3), '#b9a1f0', 'Ft');
      }
      const origin = project(-44, -10, 30);
      arrow(origin, project(-32, -10, 30), '#8fb5bd', 'x');
      arrow(origin, project(-44, 2, 30), '#82bfae', 'y');
      c.font = '9px monospace';
      c.fillStyle = '#92aeb7';
      const label = project(35, -9, 30);
      c.fillText('80 mm', label.x - 28, label.y + 16);
    }
  }

  function plot(canvas, series, {
    cursor = null,
    xLabel = 'Time [s]',
    yLabel = 'Force [N]',
    minY = null
  } = {}) {
    const {
      ctx: c,
      width: w,
      height: h
    } = context(canvas);
    const pad = {
        l: 43,
        r: 15,
        t: 14,
        b: 30
      },
      iw = w - pad.l - pad.r,
      ih = h - pad.t - pad.b;
    if (!series.length || iw <= 0 || ih <= 0) return;
    let xmax = 0,
      ymax = 0,
      ymin = 0;
    for (const s of series)
      for (const p of s.points) {
        xmax = Math.max(xmax, p[0]);
        ymax = Math.max(ymax, p[1]);
        ymin = Math.min(ymin, p[1]);
      }
    xmax = Math.max(xmax, 1e-6);
    ymax = Math.max(ymax * 1.1, .1);
    ymin = minY ?? (ymin < 0 ? ymin * 1.15 : 0);
    const px = x => pad.l + x / xmax * iw,
      py = y => pad.t + (ymax - y) / (ymax - ymin) * ih;
    c.font = '8px monospace';
    c.fillStyle = '#8da3b2';
    c.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const y = ymin + (ymax - ymin) * i / 4;
      c.beginPath();
      c.moveTo(pad.l, py(y));
      c.lineTo(w - pad.r, py(y));
      c.strokeStyle = '#273943';
      c.lineWidth = .6;
      c.stroke();
      c.fillText(y.toFixed(Math.abs(ymax) < 1 ? 2 : 1), pad.l - 8, py(y) + 3);
    }
    c.textAlign = 'center';
    for (let i = 0; i <= 4; i++) {
      const x = xmax * i / 4;
      c.fillText(x.toFixed(xmax < 2 ? 2 : 1), px(x), h - 16);
    }
    c.save();
    c.beginPath();
    c.rect(pad.l, pad.t, iw, ih);
    c.clip();
    for (const s of series) {
      c.beginPath();
      s.points.forEach(([x, y], i) => i ? c.lineTo(px(x), py(y)) : c.moveTo(px(x), py(y)));
      c.strokeStyle = s.color;
      c.lineWidth = 1.6;
      c.setLineDash(s.dash || []);
      c.stroke();
    }
    c.setLineDash([]);
    if (cursor !== null) {
      c.beginPath();
      c.moveTo(px(cursor), pad.t);
      c.lineTo(px(cursor), h - pad.b);
      c.strokeStyle = '#dfece980';
      c.setLineDash([3, 4]);
      c.stroke();
      c.setLineDash([]);
    }
    c.restore();
    c.textAlign = 'left';
    c.fillStyle = '#8da3b2';
    c.fillText(yLabel, pad.l, 9);
    c.textAlign = 'right';
    c.fillText(xLabel, w - pad.r, h - 2);
  }

  function wave(canvas, row) {
    const {
      ctx: c,
      width: w,
      height: h
    } = context(canvas);
    c.strokeStyle = '#29434a';
    c.beginPath();
    c.moveTo(0, h / 2);
    c.lineTo(w, h / 2);
    c.stroke();
    c.beginPath();
    for (let x = 0; x <= w; x++) {
      const t = x / w * .1,
        y = h / 2 - Math.sin(t * row.frequency_hz * Math.PI * 2) * row.amplitude * h * .47;
      x ? c.lineTo(x, y) : c.moveTo(x, y);
    }
    c.strokeStyle = '#62e4bd';
    c.lineWidth = 1.4;
    c.stroke();
  }
  root.HaptiSenseRender = {
    SurfaceView,
    plot,
    wave
  };
})(globalThis);
