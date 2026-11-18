/* Optional browser gate. PLAYWRIGHT_MODULE may point to the bundled workspace runtime. */
const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.DELTA_UI_URL || 'http://127.0.0.1:3010';
const output = process.env.DELTA_QA_OUTPUT || '.tmp/upgrade-ui/final';
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [], requests = [], canvasFonts = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.url().includes('/api/v2/')) requests.push(request.url()); });
  await page.exposeFunction('recordCanvasFont', value => canvasFonts.push(value));
  await page.addInitScript(() => {
    const fill = CanvasRenderingContext2D.prototype.fillText;
    CanvasRenderingContext2D.prototype.fillText = function (...args) { window.recordCanvasFont(this.font); return fill.apply(this, args); };
  });
  const results = [];
  async function open(route, ready = '.panel h2,.model-card') {
    await page.goto(base + route);
    await page.locator(ready).first().waitFor({ timeout: 90000 });
  }
  // All main screens at the five contractual widths. No API substitute is used here.
  for (const width of [320, 390, 768, 1280, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of ['/', '/stocks?ticker=FPT', '/atlas?kind=combined', '/financial', '/lab']) {
      await open(route, route.startsWith('/stocks') ? '.stock-card' : '.panel h2,.model-card');
      if(route!=='/lab') await page.locator('.chart[aria-busy="false"] canvas').first().waitFor({timeout:30000});
      const computed = await page.evaluate(() => ({
        width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
        small: [...document.querySelectorAll('body *')].filter(e => e.checkVisibility() && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 12).map(e => ({ tag: e.tagName, class: e.className, size: getComputedStyle(e).fontSize })),
      }));
      results.push({ route, ...computed });
      assert(computed.scrollWidth <= width, `Horizontal page overflow at ${route} / ${width}`);
      assert.equal(computed.small.length, 0, `UI text below 12px at ${route} / ${width}`);
      if ([390, 1440].includes(width)) await page.screenshot({ path: path.join(output, `${route.split('?')[0].slice(1) || 'home'}-${width}.png`), fullPage: true });
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  requests.length = 0;
  await open('/stocks?ticker=FPT', '.stock-card');
  assert.equal(await page.locator('.stock-card').count(), 6);
  assert.match(await page.locator('.stock-cards').innerText(), /5\.504 đ/);
  assert.match(await page.locator('.stock-header').innerText(), /95\.800 đ/);
  assert(!requests.some(u => /\/members\/|\/compare\?|\/migration\/|\/scores\/|\/peers/.test(u)), 'Deep panels fetched on Stock overview');
  await page.locator('.stock-card[data-metric="pe"] .info-tip button').focus();
  assert.match(await page.getByRole('tooltip').innerText(), /Giá \/ EPS/);
  await page.getByRole('tab', { name: 'Chỉ số tài chính', exact: true }).click();
  await page.locator('.fundamentals-table').waitFor();
  assert.match(page.url(), /tab=indicators/);
  assert.equal(await page.locator('.fundamentals-table tr[data-metric]').count(), 19);
  await page.goBack();
  await page.locator('.stock-card').first().waitFor();
  await page.getByRole('tab', { name: 'Tổng quan', exact: true }).focus();
  await page.keyboard.press('ArrowRight');
  await page.waitForURL(/tab=indicators/);
  assert.equal(await page.locator('#stock-indicators').getAttribute('aria-selected'), 'true');
  await page.getByRole('tab', { name: 'Điểm sức khỏe', exact: true }).click();
  await page.locator('.signal-list li').first().waitFor();
  assert.equal(await page.locator('.signal-list li').count(), 9);
  await page.getByRole('tab', { name: 'So sánh cùng nhóm', exact: true }).click();
  await page.locator('.peers-table tr.is-current').waitFor();
  assert.match(await page.locator('.peers-table tr.is-current').innerText(), /FPT/);
  await open('/stocks?ticker=VCB', '.stock-card');
  assert.match(await page.locator('.stock-cards').innerText(), /ROA[\s\S]*BVPS/);
  await open('/stocks?ticker=VCB&tab=scores', '#stock-panel .state-box');
  assert.match(await page.locator('#stock-panel').innerText(), /Không áp dụng/);
  await open('/stocks?ticker=BHH&tab=indicators', '.fundamentals-table');
  assert((await page.locator('.fundamentals-table .cell-missing').count()) > 0, 'Small ticker should show explicit gaps');
  // No stock page view shows internal review/package wording.
  for (const route of ['/stocks?ticker=FPT', '/stocks?ticker=FPT&tab=indicators', '/stocks?ticker=VCB&tab=scores']) {
    await open(route, '.stock-card');
    await page.waitForLoadState('networkidle');
    assert.doesNotMatch(await page.locator('main').innerText(), /review|vintage|package|cohort|pilot|sha-?256/i, `Internal wording on ${route}`);
  }
  // Resolve only the most recent ticker while earlier responses are delayed.
  await open('/stocks?ticker=VNM', '.stock-card');
  let resolveDelayed;
  const delayedDone=new Promise(resolve=>{resolveDelayed=resolve;});
  await page.route('**/api/v2/stocks/FPT/overview*', async route => {
    try { const response = await route.fetch(); await new Promise(resolve => setTimeout(resolve, 700)); await route.fulfill({ response }); }
    catch(error){if(!/already handled|cancelled|canceled|aborted|Request context disposed/.test(String(error)))throw error;}
    finally{resolveDelayed();}
  });
  const delayedStarted=page.waitForRequest(request=>new URL(request.url()).pathname.endsWith('/api/v2/stocks/FPT/overview'));
  await page.getByLabel('Tra cứu mã cổ phiếu').fill('FPT');
  await page.getByRole('button', { name: 'Xem', exact: true }).click();
  await delayedStarted;
  await page.getByLabel('Tra cứu mã cổ phiếu').fill('HPG');
  await page.getByRole('button', { name: 'Xem', exact: true }).click();
  await page.waitForURL(/ticker=HPG/);
  await page.locator('.stock-card').first().waitFor();
  await delayedDone;
  assert.match(await page.locator('.stock-title h1').innerText(), /^HPG/);
  await page.unrouteAll({behavior:'wait'});
  requests.length = 0;
  await open('/atlas?kind=combined&date=2025-12-31&cluster=2', '.size-bars');
  assert(!requests.some(u => /\/members\/|\/migration\//.test(u)), 'Deep Atlas panel fetched before opening its tab');
  await page.getByRole('tab', { name: 'Thành viên', exact: true }).click();
  await page.locator('.data-table tbody tr').first().waitFor();
  assert.equal(await page.locator('.data-table tbody tr').count(), 6);
  assert.equal(await page.getByLabel('Lọc theo cụm').inputValue(), '2');
  assert((await page.locator('.data-table thead th').count()) <= 7);
  await page.locator('.ticker-cell').first().click();
  await page.getByRole('dialog').waitFor();
  await page.keyboard.press('Tab');
  assert(await page.getByRole('dialog').evaluate(d => d.contains(document.activeElement)));
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({ state: 'detached' });
  assert(!(new URL(page.url())).searchParams.has('ticker'));
  await page.getByRole('tab', { name: 'Chất lượng', exact: true }).click();
  await page.getByRole('heading', { name: 'Chuyển dịch thành viên' }).waitFor();
  await open('/financial?year=2016&tab=compare');
  await page.getByText('Không có mô hình thị trường cho FY này', { exact: true }).waitFor();
  await page.getByText('Không có C năm 2016', { exact: true }).waitFor();
  await open('/financial?year=2025&tab=compare');
  await page.locator('.matrix-cell').first().waitFor();
  await page.locator('.matrix-cell').first().click();
  await page.locator('.table-toolbar').waitFor();
  assert.match(page.url(), /matrix_a=/);
  await page.locator('.global-search').click();
  const dialog = page.getByRole('dialog', { name: 'Tìm doanh nghiệp' });
  await dialog.waitFor();
  await dialog.getByLabel('Tìm cổ phiếu', { exact: true }).fill('FPT');
  await dialog.locator('.command-result strong').filter({ hasText: /^FPT$/ }).waitFor();
  await page.keyboard.press('Escape');
  await dialog.waitFor({ state: 'hidden' });
  assert.equal(await page.evaluate(() => document.activeElement?.className), 'global-search');
  // Service errors must remain errors, with a working retry; never become missing coverage.
  await page.route('**/api/v2/stocks/FPT/overview*', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Dịch vụ đang khởi động.' }) }));
  await page.goto(base + '/stocks?ticker=FPT');
  await page.locator('.state-box.error').first().waitFor({ timeout: 90000 });
  assert.match(await page.locator('.state-box.error').first().innerText(), /Dịch vụ đang khởi động/);
  assert.equal(await page.locator('.stock-card').count(), 0);
  await page.unroute('**/api/v2/stocks/FPT/overview*');
  await page.locator('.state-box.error').first().getByRole('button', { name: 'Thử lại' }).click();
  await page.locator('.stock-card').first().waitFor();
  // Synthetic contract fixtures stay inside this isolated browser context, never in product data.
  await page.route('**/api/v2/snapshots/combined*',async route=>{
    const response=await route.fetch(),body=await response.json();
    const labels=[2,10,18,26,34,42,50,58];
    body.points=body.points.slice(0,17).map((p,i)=>({...p,cluster:i===16?-1:labels[Math.floor(i/2)]}));
    body.snapshot={...body.snapshot,n:17,k:8,sizes:Object.fromEntries([...labels.map(id=>[String(id),2]),['-1',1]])};
    body.profiles=[...labels,-1].map(id=>({...body.profiles[0],cluster:id,size:id<0?1:2}));
    await route.fulfill({response,json:body});
  });
  await open('/atlas?kind=combined&date=2025-12-31','.size-bars');
  const colors=await page.locator('.size-bars .cluster-badge').evaluateAll(nodes=>nodes.filter(n=>!n.textContent.includes('noise')).map(n=>getComputedStyle(n).color));
  assert.equal(new Set(colors).size,8,'Sparse IDs must map to eight distinct categorical colors');
  assert.match(await page.locator('.size-bars').innerText(),/Chưa gán \/ noise/);
  await page.unrouteAll({behavior:'wait'});
  await page.route('**/api/v2/matrix/2025*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({available:true,date:'2025-12-31',year:'2025',total:6,market_labels:[2,8],financial_labels:[5,11,30],cells:[5,11,30].flatMap(financial_cluster=>[2,8].map(market_cluster=>({market_cluster,financial_cluster,n:1}))),scope:'SYNTHETIC_CONTRACT_FIXTURE',reason:'Isolated browser test fixture only'})}));
  await open('/financial?year=2025&tab=compare','.matrix-cell');
  assert.equal(await page.locator('.matrix-cell').count(),6);
  assert.match(await page.locator('.matrix-table').innerText(),/B30/);
  assert.match(await page.locator('.matrix-table').innerText(),/A8/);
  await page.unrouteAll({behavior:'wait'});
  await open('/stocks?ticker=FPT','.stock-card');
  await page.evaluate(() => { document.body.style.zoom = '2'; });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Reflow overflow at CSS zoom 200%');
  await page.screenshot({ path: path.join(output, 'fpt-css-zoom-200.png'), fullPage: true });
  await page.evaluate(()=>{document.body.style.zoom='';});
  await open('/stocks?ticker=FPT&revision=wrong','.state-box.error');
  assert.match(await page.locator('.state-box.error').innerText(),/Phiên bản trong liên kết/);
  // Real R1 source artifacts are selectable previews; baseline remains the default.
  await open('/atlas?kind=combined&date=2025-12-31','.size-bars');
  const previewOptions=await page.getByLabel('Phiên bản phân cụm').locator('option').evaluateAll(options=>options.map(o=>({value:o.value,label:o.textContent})));
  const p3=previewOptions.find(o=>o.label.includes('R1 P3'));
  assert(p3,'Reviewed R1 P3 preview was not registered');
  await page.getByLabel('Phiên bản phân cụm').selectOption(p3.value);
  await page.waitForURL(url=>url.searchParams.get('version')===p3.value);
  await page.locator('.size-bars .cluster-badge').first().waitFor();
  await page.waitForFunction(()=>document.querySelectorAll('.size-bars .cluster-badge').length===2);
  assert.match(await page.locator('.size-bars').innerText(),/622/);assert.match(await page.locator('.size-bars').innerText(),/526/);
  assert.match(await page.locator('.cluster-diagnostic').first().innerText(),/chưa promote/);
  await page.screenshot({path:path.join(output,'atlas-r1-p3-1440.png'),fullPage:true});
  await page.getByRole('tab',{name:'Hồ sơ & đối chiếu',exact:true}).click();
  await page.getByRole('heading',{name:'Peer examples đã lưu'}).waitFor();
  assert.match(await page.locator('#atlas-panel').innerText(),/FPT/);
  await page.getByRole('tab',{name:'Chất lượng',exact:true}).click();
  await page.getByText('Feature / block contribution đã lưu',{exact:true}).waitFor();
  await page.getByText('Silhouette distribution đã export',{exact:true}).waitFor();
  await page.setViewportSize({width:390,height:1000});
  await page.getByRole('tab',{name:'Khám phá',exact:true}).click();
  await page.locator('.chart[aria-busy="false"] canvas').first().waitFor();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(output,'atlas-r1-p3-390.png'),fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await open(`/stocks?ticker=FPT&kind=combined&date=2025-12-31&version=${encodeURIComponent(p3.value)}`,'.stock-card');
  assert.equal(await page.locator('.stock-card').count(),6);
  await open(`/financial?year=2025&tab=compare&version=${encodeURIComponent(p3.value)}`,'.matrix-cell');
  assert.equal(await page.locator('.matrix-cell').count(),4);
  const intersection=(await page.locator('.matrix-cell strong').first().innerText()).replace(/\./g,'');
  await page.locator('.matrix-cell').first().click();await page.locator('.table-footer').waitFor();
  assert.match((await page.locator('.table-footer').innerText()).replace(/\./g,''),new RegExp(intersection));
  await open('/atlas?kind=combined&date=2025-12-31','.size-bars');
  assert.equal(await page.locator('.size-bars .cluster-badge').count(),3,'Default baseline changed after preview selection');
  const sizes = canvasFonts.flatMap(font => [...font.matchAll(/([\d.]+)px/g)].map(match => Number(match[1])));
  assert(sizes.length > 0, 'No canvas typography was observed');
  assert(Math.min(...sizes) >= 12, `Canvas text below 12px: ${Math.min(...sizes)}`);
  assert.equal(errors.length, 0, errors.join('\n'));
  // Owner screenshots: three tickers, four tabs, desktop and phone width.
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const ticker of ['FPT', 'VCB', 'BHH']) {
      for (const tab of ['overview', 'indicators', 'scores', 'peers']) {
        await open(`/stocks?ticker=${ticker}&tab=${tab}`, '.stock-card');
        await page.waitForLoadState('networkidle');
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow ${ticker} ${tab} ${width}`);
        await page.screenshot({ path: path.join(output, `stock-${ticker}-${tab}-${width}.png`), fullPage: true });
      }
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  const report = { status: 'PASS', base, responsive: results, canvasMinimumPx: Math.min(...sizes), errors, scenarios: ['FPT six cards + tooltip', 'VCB bank cards and NOT_APPLICABLE scores', 'BHH explicit gaps', 'no review/vintage wording on stock page', 'stock screenshots FPT/VCB/BHH at 1440 and 390', 'URL Back/Forward and arrow tabs', 'stale ticker cancellation', 'deep panels not mounted/fetched', 'cluster filter and drawer keyboard', 'Financial missing years and dynamic matrix', 'command palette focus restore', '503 error/retry', 'CSS zoom 200% reflow', 'reduced motion context','mismatched bundle revision rejected','real R1 preview version selection, saved diagnostics/peers, mobile reflow, stock members, matrix membership, default baseline unchanged'],syntheticContractFixtures:['eight sparse positive labels plus separate negative/unassigned label palette','rectangular 3x2 matrix with sparse labels'], limitations: ['CSS zoom simulates reflow; browser chrome zoom and three-person usability need human acceptance.', 'Cold hosting start and public deployment not measured by this local test.'] };
  fs.writeFileSync(path.join(output, 'verification.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, responsiveCases: results.length, canvasMinimumPx: report.canvasMinimumPx, errors }, null, 2));
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });

