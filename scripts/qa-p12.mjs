import fs from 'node:fs/promises';
export const root = '/home/user/workspace/gaz-dla-przemyslu';
export const origin = 'http://127.0.0.1:9403';
export async function start(browser) {
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage();
  const report={scope:'P1.2: local Playground CLI; public URL not tested',urls:[],views:[],axe:[],hosts:[],errors:[],failedRequests:[]};
  const hosts=new Set();
  page.on('request',r=>{try{hosts.add(new URL(r.url()).host)}catch{}});
  page.on('requestfailed',r=>report.failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
  page.on('pageerror',e=>report.errors.push(e.message));
  await fs.mkdir(root+'/docs/screenshots/p12',{recursive:true});
  const source=JSON.parse(await fs.readFile(root+'/content/build-report.json','utf8'));
  const paths=[...new Set(source.items.filter(i=>['page','post'].includes(i.post_type)).map(i=>i.public_path))];
  paths.push('/category/zmiana-sprzedawcy/','/category/umowy-i-wypowiedzenia/','/category/ceny-i-rynek/','/category/biometan-i-raportowanie/','/category/sprzedaz-rezerwowa/','/komentarz-rynkowy/','/nieistniejacy-adres-p12/');
  report.audit=await (await context.request.get(origin+'/gdp-audit.json')).json();
  async function save(){report.hosts=[...hosts].sort();await fs.writeFile(root+'/docs/qa/p12-browser.json',JSON.stringify(report,null,2));}
  return {context,page,report,paths,save};
}
export async function routes(state,start=0,count=12) {
  for(const path of state.paths.slice(start,start+count)){
    const response=await state.page.goto(origin+path,{waitUntil:'networkidle'});
    const h1=await state.page.locator('h1').count();
    state.report.urls.push({path,status:response.status(),expected:path.includes('nieistniejacy')?404:200,h1,finalURL:state.page.url(),overflow:await state.page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
  }
  await state.save();
  console.log(state.report.urls.slice(start,start+count));
}
export async function views(state,slug,path,axe=false){
  for(const [device,width,height] of [['mobile',360,800],['tablet',768,1024],['desktop',1440,900]]){
    await state.page.setViewportSize({width,height});
    await state.page.goto(origin+path,{waitUntil:'networkidle'});
    await state.page.evaluate(()=>document.fonts.ready);
    const metrics=await state.page.evaluate(()=>{
      const ctas=[...document.querySelectorAll('#header a.ct-button')];
      return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,ctaAboveFold:ctas.some(a=>{let r=a.getBoundingClientRect();return r.width>0&&r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth}),tableScroll:[...document.querySelectorAll('.wp-block-table')].map(t=>({width:t.clientWidth,scroll:t.scrollWidth})),smallText:[...document.querySelectorAll('p,a,summary')].filter(e=>{const s=getComputedStyle(e);return e.getBoundingClientRect().width>0&&parseFloat(s.fontSize)<12}).map(e=>e.textContent.slice(0,70))};
    });
    state.report.views.push({slug,device,...metrics});
    await state.page.screenshot({path:`${root}/docs/screenshots/p12/${slug}-${device}.png`,fullPage:true});
    await state.page.screenshot({path:`${root}/docs/screenshots/p12/${slug}-${device}-viewport.png`});
  }
  if(axe){
    await state.page.addScriptTag({path:root+'/node_modules/axe-core/axe.min.js'});
    const result=await state.page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return {violations:r.violations,incomplete:r.incomplete,passes:r.passes.length};});
    state.report.axe.push({path,...result});
  }
  await state.save();console.log({slug,views:state.report.views.filter(v=>v.slug===slug),axe:state.report.axe.at(-1)?.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))});
}
export async function interactions(state){
  const {page}=state;
  const r={};
  await page.setViewportSize({width:360,height:800});
  await page.goto(origin+'/',{waitUntil:'networkidle'});
  await page.locator('[data-id="trigger"]:visible').first().click();
  r.menuVisibleLinks=await page.locator('#offcanvas a:visible').count();
  await page.screenshot({path:root+'/docs/screenshots/p12/mobile-menu.png'});
  await page.keyboard.press('Escape');
  await page.goto(origin+'/oferta/cena-stala/',{waitUntil:'networkidle'});
  const summary=page.locator('details summary').first();
  await summary.focus();await page.keyboard.press('Enter');
  r.faqKeyboardOpen=await summary.evaluate(e=>e.parentElement.open);
  await page.keyboard.press('Enter');
  r.faqKeyboardClosed=await summary.evaluate(e=>!e.parentElement.open);
  await page.mouse.wheel(0,1200);
  await page.waitForTimeout(350);
  r.sticky=await page.locator('#header').evaluate(e=>({top:e.getBoundingClientRect().top,shrunk:document.documentElement.classList.contains('gdp-scrolled')}));
  await page.goto(origin+'/wiedza/',{waitUntil:'networkidle'});
  await page.locator('input[type="search"]').first().fill('sprzedawcę');
  await page.locator('.wp-block-search__button').first().click();
  await page.waitForLoadState('networkidle');
  r.search={url:page.url(),text:(await page.locator('#main').innerText()).slice(0,1400)};
  await page.goto(origin+'/?s=gdpbraktestowegoslowa',{waitUntil:'networkidle'});
  r.emptySearch={status:'rendered',text:(await page.locator('#main').innerText()).slice(0,800)};
  state.report.interactions=r;
  await state.save();console.log(r);
}
