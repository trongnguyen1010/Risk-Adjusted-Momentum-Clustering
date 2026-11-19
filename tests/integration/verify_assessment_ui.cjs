/* Optional Assessment UI regression gate. Requires a running local UI/API and Playwright. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const repoRoot = process.env.DELTA_REPO_ROOT || path.resolve(__dirname, '../..');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || require.resolve('playwright', {
  paths: [path.join(repoRoot, 'web/frontend')],
});
const { chromium } = require(playwrightModule);
const base = process.env.DELTA_UI_URL || 'http://127.0.0.1:3000';
const api = process.env.DELTA_API_URL || 'http://127.0.0.1:8010';
const supportApiUrl = process.env.DELTA_SUPPORT_API_URL || api;
const output = process.env.DELTA_QA_OUTPUT || 'tests/integration/evidence/assessment-uat';
const featureIds = [
  'roe', 'roa', 'gross_margin', 'net_margin', 'debt_to_equity', 'current_ratio',
  'asset_turnover', 'revenue_growth', 'cfo_to_ni', 'mom_21', 'mom_63', 'mom_126',
  'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21', 'downside_vol_63',
];
fs.mkdirSync(path.join(output, 'screenshots'), { recursive: true });

async function apiJson(ticker, query = '') {
  const response = await fetch(`${api}/api/v2/stocks/${ticker}/assessment${query}`);
  return { status: response.status, body: await response.json() };
}

async function getCatalog() {
  const response = await fetch(`${api}/api/v2/catalog`);
  assert.equal(response.status, 200, 'catalog support endpoint must be available');
  return response.json();
}

(async () => {
  const catalog = await getCatalog();
  const supportApiVersion = catalog.metadata?.version;
  assert.ok(supportApiVersion, 'catalog response must identify its support API dataset');
  assert.notEqual(supportApiVersion, 'ui-smoke-bundle', 'synthetic shell catalog must not be used');
  const a32 = await apiJson('A32');
  const a32Short = await apiJson('A32', '?lookback_years=5');
  const aam = await apiJson('AAM');
  const vcb = await apiJson('VCB');
  const fpt = await apiJson('FPT');
  const wrongRevision = await apiJson('A32', '?revision=assessment-ui-wrong-revision');
  const releasePointer = JSON.parse(fs.readFileSync(path.join(repoRoot, 'configs/product/assessment_release_v1.json'), 'utf8'));
  const matchingRevision = await apiJson('A32', `?revision=${encodeURIComponent(releasePointer.release_revision)}`);
  assert.equal(a32.status, 200, 'A32 must exist in the pinned Assessment release');
  assert.equal(fpt.status, 200, 'FPT must exist in the pinned Assessment release');
  assert.equal(a32Short.status, 200);
  assert.equal(aam.status, 200);
  assert.equal(aam.body.assessment_status, 'INSUFFICIENT_EVIDENCE');
  assert.equal(vcb.status, 404, 'VCB absence in this release must be rendered as missing');
  assert.equal(wrongRevision.status, 409, 'wrong release revision must be rejected');
  assert.equal(matchingRevision.status, 200, 'the pinned Assessment release revision must be accepted');
  assert.equal(matchingRevision.body.references.release_revision, releasePointer.release_revision);
  assert.deepEqual(a32.body.features.map(feature => feature.feature_id).sort(), [...featureIds].sort());
  assert.equal(a32.body.references.release_revision, releasePointer.release_revision);
  assert.equal(a32.body.references.manifest_sha256, releasePointer.manifest_sha256);
  assert.equal(a32.body.references.deterministic_content_sha256, releasePointer.deterministic_content_sha256);
  assert.equal(a32.body.as_of, releasePointer.as_of);
  assert.equal(a32.body.availability_status, 'READY');
  for (const field of ['ticker', 'as_of', 'assessment_context', 'assessment_status', 'references']) {
    assert.deepEqual(a32Short.body[field], a32.body[field], `${field} must not change with lookback`);
  }

  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}),
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const screenshots = [];
  const capture = async name => {
    const file = path.join(output, 'screenshots', `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    screenshots.push(file);
  };
  try {
    await page.goto(`${base}/stocks?ticker=A32&tab=assessment&lookback_years=10&metric=roe`);
    await page.locator('#assessment-feature-selector').waitFor();
    await page.getByLabel(`Availability: ${'Dữ liệu sẵn sàng'}`).waitFor();
    assert.equal(await page.locator('#assessment-feature-selector option').count(), 18);
    assert.equal(await page.locator('#assessment-lookback-selector option').count(), 2);
    assert.equal(await page.locator('section[aria-label="Biểu đồ một chỉ số Assessment"] .chart').count(), 1);
    const pinnedRevision = a32.body.references.release_revision;
    assert.ok(pinnedRevision, 'release revision pin must be present');
    await capture('a32-desktop');

    await page.goto(`${base}/stocks?ticker=FPT&tab=assessment`);
    await page.getByRole('heading', { name: 'Assessment · FPT' }).waitFor();
    await capture('fpt-current');
    await page.goto(`${base}/stocks?ticker=A32&tab=assessment&lookback_years=10&metric=roe`);
    await page.locator('#assessment-feature-selector').waitFor();

    await page.selectOption('#assessment-lookback-selector', '5');
    await page.waitForURL(/lookback_years=5/);
    assert.match(page.url(), /metric=roe/);
    assert.equal(await page.locator('section[aria-label="Biểu đồ một chỉ số Assessment"] .chart').count(), 1);
    await page.goBack();
    await page.waitForURL(/lookback_years=10/);
    await page.goForward();
    await page.waitForURL(/lookback_years=5/);

    await page.selectOption('#assessment-feature-selector', 'mom_21');
    await page.waitForURL(/metric=mom_21/);

    await page.getByRole('tab', { name: /TỔNG QUAN/i }).click();
    await page.waitForURL(/tab=overview/);
    await page.getByRole('tab', { name: /ĐÁNH GIÁ ĐẦU TƯ/i }).click();
    await page.waitForURL(/tab=assessment/);
    await page.getByRole('heading', { name: 'Assessment · A32' }).waitFor();
    assert.equal(await page.locator('section[aria-label="Biểu đồ một chỉ số Assessment"] .chart').count(), 1);

    await page.goto(`${base}/stocks?ticker=AAM&tab=assessment`);
    await page.getByRole('region', { name: 'Assessment cho AAM' })
      .getByLabel(/Kết luận Assessment: Chưa đủ bằng chứng/).first().waitFor();
    await capture('aam-insufficient');

    await page.goto(`${base}/stocks?ticker=VCB&tab=assessment`);
    await page.getByText(/không có dữ liệu|không tìm thấy/i).first().waitFor();
    await capture('vcb-missing');

    // This intercepted payload is intentionally a presentation fixture, not a pinned release result.
    await page.route('**/api/v2/stocks/A32/assessment*', async route => {
      const response = await route.fetch();
      const body = await response.json();
      body.availability_status = 'STALE';
      await route.fulfill({ response, json: body });
    });
    await page.goto(`${base}/stocks?ticker=A32&tab=assessment`);
    await page.getByText(/đang hiển thị dữ liệu cũ/i).waitFor();
    await capture('a32-stale-fixture');
    await page.unrouteAll();

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/stocks?ticker=A32&tab=assessment`);
    await page.locator('#assessment-feature-selector').waitFor();
    const widths = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
    assert.ok(widths.document <= widths.viewport + 1, `horizontal page overflow: ${JSON.stringify(widths)}`);
    await capture('a32-mobile');

    await page.locator('#assessment-feature-selector').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'assessment-lookback-selector');
    await page.getByRole('group', { name: 'Giao diện' }).getByRole('button', { name: 'Sáng' }).click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
    await capture('a32-mobile-light');
    assert.deepEqual(errors, [], 'browser console must not contain uncaught page errors');

    // A delayed FPT payload must not become visible after navigation to A32.
    let delayedStarted;
    const started = new Promise(resolve => { delayedStarted = resolve; });
    await page.route('**/api/v2/stocks/FPT/assessment*', async route => {
      const response = await route.fetch();
      delayedStarted();
      await new Promise(resolve => setTimeout(resolve, 900));
      try { await route.fulfill({ response }); } catch { /* request may be aborted after ticker changes */ }
    });
    await page.goto(`${base}/stocks?ticker=FPT&tab=assessment`);
    await started;
    await page.getByLabel('Tra cứu mã cổ phiếu').fill('A32');
    await page.locator('form.stock-search button').click();
    await page.waitForURL(/ticker=A32/);
    await page.getByRole('tab', { name: /ĐÁNH GIÁ ĐẦU TƯ/i }).click();
    await page.waitForURL(/tab=assessment/);
    await page.getByRole('heading', { name: 'Assessment · A32' }).waitFor();
    await new Promise(resolve => setTimeout(resolve, 1100));
    assert.equal(await page.getByRole('heading', { name: 'Assessment · A32' }).count(), 1);
    await page.unrouteAll();

    fs.writeFileSync(path.join(output, 'response-pins.json'), JSON.stringify({
      release_revision: a32.body.references.release_revision,
      manifest_sha256: a32.body.references.manifest_sha256,
      deterministic_content_sha256: a32.body.references.deterministic_content_sha256,
      as_of: a32.body.as_of,
      assessment_context: a32.body.assessment_context,
      support_api_version: supportApiVersion,
      support_api_url: supportApiUrl,
      verified_tickers: ['FPT', 'A32', 'AAM'],
      missing_tickers: ['VCB'],
      synthetic_stale_fixture: true,
    }, null, 2) + '\n');
    fs.writeFileSync(path.join(output, 'ui-result.json'), JSON.stringify({
      status: 'PASS', screenshots, widths, support_api_version: supportApiVersion, checks: [
        '18 features', '5/10 lookback URL and history navigation', 'one chart',
        'INSUFFICIENT_EVIDENCE', 'missing ticker', 'matching revision 200 / mismatch 409',
        'stale presentation fixture', 'mobile width', 'keyboard focus', 'light theme',
      ],
    }, null, 2) + '\n');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
