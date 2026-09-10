/* Exercise the static workbench with a real Chromium browser in CI. */
const assert = require('node:assert/strict'),
  fs = require('node:fs/promises'),
  path = require('node:path');
const {
  chromium
} = require('playwright');
(async () => {
  const base = process.env.HAPTISENSE_BASE_URL || 'http://127.0.0.1:8000';
  const out = process.env.HAPTISENSE_BROWSER_OUTPUT || 'test-results/browser';
  await fs.mkdir(out, {
    recursive: true
  });
  const browser = await chromium.launch({
      headless: true
    }),
    checks = [];
  try {
    const page = await browser.newPage({
        viewport: {
          width: 1440,
          height: 1050
        },
        deviceScaleFactor: 1
      }),
      errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => {
      if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`);
    });
    await page.goto(base + '/workbench.html');
    await page.getByRole('heading', {
      name: 'Virtual contact field'
    }).waitFor();
    assert.equal((await page.locator('#samples').innerText()).replaceAll(',', ''), '2001');
    assert.ok(parseFloat(await page.locator('#force').innerText()) > 0);
    checks.push('initial model and telemetry');
    await page.screenshot({
      path: path.join(out, 'workbench-desktop.png'),
      fullPage: true
    });
    const before = await page.locator('#peak').innerText();
    await page.getByLabel('ILLUSTRATIVE MATERIAL').selectOption('fibrous');
    assert.notEqual(await page.locator('#peak').innerText(), before);
    await page.getByLabel('CONTACT LAW').selectOption('elastic');
    assert.equal(await page.locator('#p-tau').isDisabled(), true);
    assert.equal(await page.locator('#memory').innerText(), '0.000 N');
    checks.push('presets and elastic memory');
    await page.locator('#p-speed').focus();
    await page.locator('#p-speed').press('Home');
    assert.equal(await page.locator('#amplitude').innerText(), '0.000');
    checks.push('zero speed removes vibration');
    await page.getByRole('button', {
      name: 'Reset',
      exact: true
    }).click();
    await page.locator('#timeline').focus();
    await page.locator('#timeline').press('Home');
    assert.equal(await page.locator('#force').innerText(), '0.00 N');
    await page.getByRole('button', {
      name: 'Play simulation',
      exact: true
    }).click();
    await page.waitForFunction(() => parseFloat(document.querySelector('#time-label').textContent) > .15);
    await page.getByRole('button', {
      name: 'Pause simulation',
      exact: true
    }).click();
    checks.push('scrub, release, play and pause');
    await page.getByRole('button', {
      name: '02 Model comparison'
    }).click();
    assert.equal(await page.locator('#comparison-body tr').count(), 3);
    await page.screenshot({
      path: path.join(out, 'workbench-comparison.png'),
      fullPage: true
    });
    checks.push('comparison table and plots');
    await page.getByRole('button', {
      name: '03 Perceptual protocol'
    }).click();
    assert.equal(await page.locator('#staircase').isVisible(), true);
    checks.push('synthetic protocol view');
    await page.getByRole('button', {
      name: '01 Contact studio'
    }).click();
    await page.getByRole('button', {
      name: 'Reset',
      exact: true
    }).click();
    const jp = page.waitForEvent('download');
    await page.getByRole('button', {
      name: 'Export session'
    }).click();
    const jpfile = path.join(out, 'export-session.json');
    await (await jp).saveAs(jpfile);
    const session = JSON.parse(await fs.readFile(jpfile, 'utf8'));
    assert.equal(session.evidence, 'synthetic_computational');
    assert.equal(session.rows.length, 2001);
    checks.push('complete JSON export');
    const cp = page.waitForEvent('download');
    await page.getByRole('button', {
      name: 'Download trace CSV'
    }).click();
    await (await cp).saveAs(path.join(out, 'trace.csv'));
    const lines = (await fs.readFile(path.join(out, 'trace.csv'), 'utf8')).trim().split('\n');
    assert.equal(lines.length, 2002);
    assert.ok(lines[0].includes('normal_n'));
    checks.push('complete CSV export');
    session.config.stiffness = 800;
    session.rows[0].command_n = 999;
    await page.locator('#import-session').setInputFiles({
      name: 'restore.json',
      mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(session))
    });
    await page.getByRole('status').filter({
      hasText: 'recomputed'
    }).waitFor();
    assert.equal(await page.locator('#o-stiffness').innerText(), '800 N/m');
    assert.equal(await page.locator('#force').innerText(), '0.00 N');
    checks.push('import recomputes tampered results');
    await page.locator('#import-session').setInputFiles({
      name: 'invalid.json',
      mimeType: 'application/json',
      buffer: Buffer.from('{"schema":"invalid"}')
    });
    await page.getByRole('status').filter({
      hasText: 'Import rejected'
    }).waitFor();
    assert.equal(await page.locator('#o-stiffness').innerText(), '800 N/m');
    checks.push('invalid import preserves prior state');
    for (const width of [390, 768, 1024]) {
      await page.setViewportSize({
        width,
        height: 900
      });
      const dims = await page.evaluate(() => ({
        width: innerWidth,
        scroll: document.documentElement.scrollWidth
      }));
      assert.ok(dims.scroll <= dims.width + 1, `overflow at ${width}: ${JSON.stringify(dims)}`);
      await page.screenshot({
        path: path.join(out, `workbench-${width}.png`),
        fullPage: true
      });
      checks.push(`layout at ${width}px`);
    }
    assert.deepEqual(errors, []);
    checks.push('no browser exceptions or resource errors');
    const report = {
      status: 'passed',
      browser: await browser.version(),
      checks
    };
    await fs.writeFile(path.join(out, 'browser-report.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    await fs.writeFile(path.join(out, 'browser-report.json'), JSON.stringify({
      status: 'failed',
      completed: checks,
      error: error.stack
    }, null, 2));
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
