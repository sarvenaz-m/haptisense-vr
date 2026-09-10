(() => {
  'use strict';
  const M = HaptiSenseResearch,
    R = HaptiSenseRender,
    $ = id => document.getElementById(id);
  const names = {
    sls: 'Standard linear solid',
    kelvin: 'Kelvin–Voigt',
    elastic: 'Nonlinear elastic'
  };
  const colors = {
    sls: '#62e4bd',
    kelvin: '#ecc587',
    elastic: '#b9a1f0'
  };
  const presets = {
    soft: {
      stiffness: 650,
      damping: 7,
      friction: .18,
      roughness: .38,
      spatial: 1500
    },
    fibrous: {
      stiffness: 950,
      damping: 11,
      friction: .26,
      roughness: .72,
      spatial: 2200
    },
    membrane: {
      stiffness: 1200,
      damping: 5,
      friction: .12,
      roughness: .16,
      spatial: 900
    }
  };
  const sliders = [
    ['stiffness', 'Equilibrium stiffness', 100, 1800, 10, 'N/m', 1],
    ['depth', 'Peak indentation', 1, 10, .1, 'mm', 1000],
    ['tau', 'Relaxation time', .02, 1, .01, 's', 1],
    ['roughness', 'Texture roughness', 0, 1, .01, '', 1],
    ['speed', 'Scan speed', 0, 100, 1, 'mm/s', 1000]
  ];
  let config = {
      ...M.defaults
    },
    protocol = 'hold',
    session = M.simulate(config, protocol),
    comparisons = [],
    index = 650,
    playing = false,
    last = null,
    tab = 'contact';
  let notifyTimer;

  function notice(message, error = false) {
    $('notice').textContent = message;
    $('notice').classList.toggle('error', error);
    clearTimeout(notifyTimer);
  }
  for (const [key, label, min, max, step, unit, scale] of sliders) {
    const wrap = document.createElement('div');
    wrap.innerHTML = `<div class="slider-heading"><label for="p-${key}">${label}</label><output id="o-${key}"></output></div><input id="p-${key}" type="range" min="${min}" max="${max}" step="${step}"><div class="range-limits"><span>${min} ${unit}</span><span>${max} ${unit}</span></div>`;
    $('sliders').append(wrap);
    $(`p-${key}`).addEventListener('input', () => {
      config[key] = Number($(`p-${key}`).value) / scale;
      $('preset').value = 'custom';
      recompute();
    });
  }

  function updateControls() {
    $('model').value = config.model;
    $('protocol').value = protocol;
    for (const [key, , min, max, step, unit, scale] of sliders) {
      const el = $(`p-${key}`),
        value = config[key] * scale;
      // Imported valid scientific parameters may extend beyond UI defaults.
      el.min = Math.min(min, value);
      el.max = Math.max(max, value);
      el.value = value;
      $(`o-${key}`).textContent = `${value.toFixed(step<1?2:0)} ${unit}`;
    }
    $('p-tau').disabled = config.model !== 'sls';
    $('formula').textContent = config.model === 'sls' ? 'F = k(d + βd³) + q' : config.model === 'kelvin' ? 'F = k(d + βd³) + c·v₊' : 'F = k(d + βd³)';
    $('law-note').textContent = config.model === 'sls' ? 'Material memory relaxes during the hold.' : config.model === 'kelvin' ? 'Damping is applied during approach only.' : 'Instantaneous response; no material memory.';
    document.querySelector('.rate').innerHTML = `${(1000/config.rate).toFixed(config.rate===500?0:2)} ms<span>MODEL STEP</span>`;
  }

  function recompute() {
    session = M.simulate(config, protocol);
    comparisons = ['sls', 'kelvin', 'elastic'].map(model => M.simulate({
      ...config,
      model
    }, protocol));
    $('timeline').max = session.rows.length - 1;
    index = Math.min(index, session.rows.length - 1);
    updateControls();
    const m = session.metrics;
    $('peak').textContent = m.peak_command_n.toFixed(3) + ' N';
    $('rms').textContent = m.rms_command_n.toFixed(3) + ' N';
    $('limited').textContent = `${m.limited_samples} / ${m.samples}`;
    $('samples').textContent = m.samples.toLocaleString();
    render();
  }
  const scene = new R.SurfaceView($('scene'), () => render());

  function series(run, key, color, x = 't_s', scale = 1) {
    return {
      color,
      points: run.rows.map(r => [r[x] * scale, r[key]])
    };
  }

  function render() {
    if (tab === 'contact') {
      const r = session.rows[Math.round(index)];
      $('timeline').value = Math.round(index);
      $('time-label').textContent = r.t_s.toFixed(3) + ' s';
      $('force').innerHTML = r.command_n.toFixed(2) + ' <small>N</small>';
      $('force-meter').style.width = (r.command_n / config.force_limit * 100) + '%';
      $('force-meter').style.background = r.limited ? '#ecc587' : '#62e4bd';
      $('limit-state').textContent = r.limited ? 'Model command limiter active' : 'Within model command limit';
      $('depth').textContent = (r.depth_m * 1000).toFixed(2) + ' mm';
      $('elastic').textContent = r.elastic_n.toFixed(3) + ' N';
      $('memory').textContent = r.memory_n.toFixed(3) + ' N';
      $('friction').textContent = r.friction_n.toFixed(3) + ' N';
      $('frequency').textContent = r.frequency_hz.toFixed(1);
      $('amplitude').textContent = r.amplitude.toFixed(3);
      scene.draw(r);
      R.wave($('wave'), r);
      R.plot($('trace'), [series(session, 'command_n', '#62e4bd'), series(session, 'normal_n', '#ecc587'), series(session, 'memory_n', '#b9a1f0')], {
        cursor: r.t_s
      });
    } else if (tab === 'compare') {
      R.plot($('comparison-chart'), comparisons.map(s => series(s, 'normal_n', colors[s.config.model])));
      R.plot($('hysteresis-chart'), comparisons.map(s => series(s, 'normal_n', colors[s.config.model], 'depth_m', 1000)), {
        xLabel: 'Penetration [mm]'
      });
      $('comparison-body').replaceChildren(...comparisons.map(s => {
        const m = s.metrics,
          tr = document.createElement('tr');
        for (const value of [names[s.config.model], m.peak_command_n.toFixed(3), m.rms_command_n.toFixed(3), m.limited_samples, (m.positive_command_work_j * 1000).toFixed(3)]) {
          const td = document.createElement('td');
          td.textContent = value;
          tr.append(td);
        }
        return tr;
      }));
    } else {
      const data = HaptiSensePsychophysics;
      R.plot($('staircase'), [{
        color: '#62e4bd',
        points: data.visual.map((v, i) => [i + 1, v])
      }, {
        color: '#ecc587',
        points: data.haptic.map((v, i) => [i + 1, v])
      }], {
        xLabel: 'Trial',
        yLabel: 'Stimulus difference'
      });
    }
  }

  function pause() {
    playing = false;
    last = null;
    $('play').textContent = '▶';
    $('play').setAttribute('aria-label', 'Play simulation');
  }
  $('play').addEventListener('click', () => {
    if (playing) {
      pause();
      return;
    }
    if (index >= session.rows.length - 1) index = 0;
    playing = true;
    last = null;
    $('play').textContent = 'Ⅱ';
    $('play').setAttribute('aria-label', 'Pause simulation');
  });
  $('timeline').addEventListener('input', () => {
    pause();
    index = Number($('timeline').value);
    render();
  });
  $('preset').addEventListener('change', () => {
    if (presets[$('preset').value]) {
      Object.assign(config, presets[$('preset').value]);
      recompute();
    }
  });
  $('model').addEventListener('change', () => {
    config.model = $('model').value;
    recompute();
  });
  $('protocol').addEventListener('change', () => {
    protocol = $('protocol').value;
    pause();
    recompute();
  });
  $('reset').addEventListener('click', () => {
    config = {
      ...M.defaults
    };
    protocol = 'hold';
    index = 650;
    pause();
    $('preset').value = 'soft';
    recompute();
    notice('Default experiment restored.');
  });
  $('camera-reset').addEventListener('click', () => scene.reset());
  document.querySelectorAll('[data-tab]').forEach(button => button.addEventListener('click', () => {
    pause();
    tab = button.dataset.tab;
    document.querySelectorAll('[data-tab]').forEach(b => {
      b.classList.toggle('selected', b === button);
      b.setAttribute('aria-pressed', String(b === button));
    });
    for (const key of ['contact', 'compare', 'protocol']) $(`${key}-view`).hidden = key !== tab;
    render();
  }));

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], {
        type
      })),
      a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    notice(`Exported ${name}. Computational data only.`);
  }
  $('export-json').addEventListener('click', () => download('haptisense-session.json', JSON.stringify(session, null, 2), 'application/json'));
  $('export-csv').addEventListener('click', () => download('haptisense-trace.csv', M.csv(session), 'text/csv'));
  $('export-comparison').addEventListener('click', () => download('haptisense-comparison.json', JSON.stringify({
    schema: 'haptisense.comparison.v1',
    evidence: 'synthetic_computational',
    design: 'same trajectory and shared parameters; model family varies',
    runs: comparisons
  }, null, 2), 'application/json'));
  $('import-session').addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      if (file.size > 8000000) throw Error('Session exceeds 8 MB');
      const restored = M.restore(await file.text());
      config = restored.config;
      protocol = restored.protocol;
      index = 0;
      pause();
      $('preset').value = 'custom';
      recompute();
      notice('Session parameters restored; every result recomputed locally.');
    } catch (error) {
      notice(`Import rejected: ${error.message}`, true);
    } finally {
      e.target.value = '';
    }
  });
  window.addEventListener('resize', () => render());
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) pause();
  });

  function frame(now) {
    if (playing && tab === 'contact') {
      if (last !== null) index += Math.min((now - last) / 1000, .1) * config.rate;
      last = now;
      if (index >= session.rows.length - 1) {
        index = session.rows.length - 1;
        pause();
      }
      render();
    }
    requestAnimationFrame(frame);
  }
  recompute();
  requestAnimationFrame(frame);
})();
