/* Retrospective HEAD baseline and upgraded production build, same pinned local API. */
const fs=require('fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
  const rows=[];
  for(const [version,origin] of [['baseline_HEAD','http://127.0.0.1:3011'],['upgrade','http://127.0.0.1:3010']]){
    const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const page=await context.newPage();
    for(const route of ['/','/stocks?ticker=FPT','/atlas?kind=combined','/financial']){
      // Warm the backend and browser asset caches; retain this separate from the three samples.
      await page.goto(origin+route);await page.locator('canvas').first().waitFor({timeout:90000});await page.waitForLoadState('networkidle');
      for(let sample=0;sample<3;sample++){
        const start=performance.now();await page.goto(origin+route);await page.locator('canvas').first().waitFor({timeout:90000});
        if(route.startsWith('/stocks'))await page.locator('.indicator-card').first().waitFor();
        const primaryMs=performance.now()-start;
        await page.waitForLoadState('networkidle');
        const resources=await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.name.includes('/api/v2/')).map(r=>({url:r.name,duration:r.duration,encodedBodySize:r.encodedBodySize,transferSize:r.transferSize})));
        rows.push({version,route,sample,primaryMs,apiRequests:resources.length,apiEncodedBytes:resources.reduce((a,r)=>a+r.encodedBodySize,0),resources});
      }
    }
    await context.close();
  }
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();await page.goto('http://127.0.0.1:3010/atlas?kind=combined');await page.locator('canvas').first().waitFor();
  await page.getByRole('tab',{name:'Chất lượng',exact:true}).click();await page.getByRole('heading',{name:'Chuyển dịch thành viên'}).waitFor();await page.waitForLoadState('networkidle');
  await page.getByRole('tab',{name:'Khám phá',exact:true}).click();await page.locator('canvas').first().waitFor();
  const cachedTabMs=await page.evaluate(async()=>{
    const start=performance.now();document.getElementById('atlas-quality').click();
    await new Promise(resolve=>{const check=()=>{if(document.querySelector('#atlas-panel .migration-summary')||document.querySelector('#atlas-panel .data-table tbody tr'))resolve();else requestAnimationFrame(check);};check();});
    return performance.now()-start;
  });
  await page.getByRole('tab',{name:'Khám phá',exact:true}).click();await page.locator('canvas').first().waitFor();
  const chartInteractionMs=await page.evaluate(async()=>{const canvas=document.querySelector('canvas'),r=canvas.getBoundingClientRect(),start=performance.now();canvas.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));return performance.now()-start;});
  const median=values=>[...values].sort((a,b)=>a-b)[Math.floor(values.length/2)];
  const summary=[];
  for(const version of ['baseline_HEAD','upgrade'])for(const route of ['/','/stocks?ticker=FPT','/atlas?kind=combined','/financial']){
    const selected=rows.filter(r=>r.version===version&&r.route===route);summary.push({version,route,medianPrimaryMs:median(selected.map(r=>r.primaryMs)),medianApiRequests:median(selected.map(r=>r.apiRequests)),medianApiEncodedBytes:median(selected.map(r=>r.apiEncodedBytes))});
  }
  const report={conditions:'Retrospective HEAD build vs upgraded production build; Edge headless, localhost API, 1440x1000, no network/CPU throttle, reduced motion, warm server and asset cache, 3 hard navigations per route. This is not production or hosting cold-start measurement.',summary,cachedTabMs,chartInteractionMs,chartInteractionDefinition:'Synthetic mousemove handler plus two animation frames; not a full end-to-end tooltip latency benchmark.',rows};
  fs.writeFileSync(process.env.DELTA_PERFORMANCE_OUTPUT||'.tmp/upgrade-ui/performance.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify({summary,cachedTabMs,chartInteractionMs},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
