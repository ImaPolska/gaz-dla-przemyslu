// Read-only browser verification. Execute from the persistent Playwright REPL:
// var qa=await import('/absolute/project/scripts/qa.mjs'); await qa.run(browser);
export async function run(browser, root='/home/user/workspace/gaz-dla-przemyslu') {
  const fs=await import('node:fs/promises');
  const report={scope:'P1.1 local CLI; not a public blueprint-url test',directions:{}};
  const sources=JSON.parse(await fs.readFile(root+'/content/build-report.json','utf8'));
  const paths=['/',...sources.items.filter(i=>i.post_type==='page'||i.post_type==='post').map(i=>i.public_path)];
  await fs.mkdir(root+'/docs/screenshots',{recursive:true});
  for (const [direction,port] of [['A',9400],['B',9401],['C',9402]]) {
    const origin='http://127.0.0.1:'+port;
    const context=await browser.newContext({viewport:{width:1440,height:900}});
    const page=await context.newPage();
    const hosts=new Set(),failures=[],errors=[];
    page.on('request',r=>{try{hosts.add(new URL(r.url()).host)}catch{}});
    page.on('requestfailed',r=>failures.push({url:r.url(),error:r.failure()?.errorText}));
    page.on('pageerror',e=>errors.push(e.message));
    const result={urls:[],views:[],hosts:[],failedRequests:failures,pageErrors:errors};
    result.audit=await (await context.request.get(origin+'/gdp-audit.json')).json();
    for (const path of paths) {
      const response=await page.goto(origin+path,{waitUntil:'networkidle'});
      result.urls.push({path,status:response.status(),finalURL:page.url(),h1:await page.locator('h1').count()});
    }
    for(const [slug,path] of [['home','/'],['cena-stala','/oferta/cena-stala/']]) {
      for(const [device,width,height] of [['desktop',1440,900],['mobile',360,800],['tablet',768,1024]]) {
        await page.setViewportSize({width,height});
        await page.goto(origin+path,{waitUntil:'networkidle'});
        await page.evaluate(()=>document.fonts.ready);
        await page.evaluate(()=>scrollTo(0,0));
        const metrics=await page.evaluate(()=>{
          const hero=document.querySelector('.gdp-hero,.gdp-product-hero');
          const ctas=[...document.querySelectorAll('a')].filter(a=>['Wgraj fakturę','Oferta w 24 h'].includes(a.textContent.trim()));
          const visible=ctas.some(a=>{let r=a.getBoundingClientRect();return r.width>0&&r.height>0&&r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth});
          return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,
            ctaAboveFold:visible,heroLeft:hero.getBoundingClientRect().left,
            palette:getComputedStyle(document.body).getPropertyValue('--theme-palette-color-1').trim(),
            font:getComputedStyle(document.body).fontFamily,
            heroHeading:getComputedStyle(hero.querySelector('h1')).fontFamily,
            finalHeading:document.querySelector('.gdp-final h2')?.textContent};
        });
        result.views.push({slug,device,...metrics});
        if(device!=='tablet') {
          await page.screenshot({path:`${root}/docs/screenshots/${direction}-${slug}-${device}.png`,fullPage:true});
          if(slug==='home')await page.screenshot({path:`${root}/docs/qa/${direction}-home-${device}-viewport.png`});
        }
      }
    }
    // Read-only interaction checks: navigation, mobile drawer, native FAQ, sticky.
    await page.goto(origin+'/',{waitUntil:'networkidle'});
    await page.setViewportSize({width:360,height:800});
    const trigger=page.locator('[data-id="trigger"]').filter({visible:true}).first();
    result.mobileMenu={present:await trigger.count()};
    if(await trigger.count()) {
      await trigger.click();
      result.mobileMenu.open=await page.locator('#offcanvas').evaluate(e=>e.className);
      result.mobileMenu.visibleLinks=await page.locator('#offcanvas a:visible').count();
      await page.keyboard.press('Escape');
    }
    await page.goto(origin+'/oferta/cena-stala/',{waitUntil:'networkidle'});
    const summary=page.locator('details summary').first();
    if(await summary.count()){
      await summary.click();
      result.faqOpens=await summary.evaluate(e=>e.parentElement.open);
    }
    await page.evaluate(()=>scrollTo(0,1000));
    await page.waitForTimeout(200);
    result.sticky=await page.evaluate(()=>({classApplied:document.documentElement.classList.contains('gdp-scrolled'),top:document.querySelector('#header').getBoundingClientRect().top}));
    result.hosts=[...hosts].sort();
    result.pass=result.audit.pass&&result.urls.every(r=>r.status===200)&&result.views.every(v=>v.h1===1&&v.scrollWidth<=v.width&&v.ctaAboveFold)&&failures.length===0&&errors.length===0;
    report.directions[direction]=result;
    await context.close();
    await fs.writeFile(root+'/docs/qa/browser-runtime.json',JSON.stringify(report,null,2));
    console.log(direction,JSON.stringify({pass:result.pass,urls:result.urls.length,views:result.views,hosts:result.hosts,failures,errors}));
  }
  return report;
}
