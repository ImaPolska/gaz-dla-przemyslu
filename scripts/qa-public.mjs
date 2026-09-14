const fs=await import('node:fs/promises');
const root='/home/user/workspace/gaz-dla-przemyslu';
export async function start(browser,key,url){
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage();
  const result={key,url,started:new Date().toISOString(),errors:[],resources:[]};
  page.on('pageerror',e=>result.errors.push(String(e)));
  page.on('response',async r=>{
    if(r.url().startsWith('https://raw.githubusercontent.com/ImaPolska/')){
      const h=await r.allHeaders();
      result.resources.push({url:r.url(),status:r.status(),cors:h['access-control-allow-origin']});
    }
  });
  await page.goto(url,{waitUntil:'domcontentloaded'});
  return {context,page,result};
}
export async function finish(state){
  const {page,result}=state;
  await page.frameLocator('iframe').first().frameLocator('iframe').first().locator('#main h1').waitFor({timeout:180000});
  state.frame=page.frames().find(f=>f.url().includes('/scope:'));
  result.initialH1=await state.frame.locator('#main h1').innerText();
  result.initialFrame=state.frame.url();
  result.ready=new Date().toISOString();
  const auditCode=await fs.readFile(root+'/scripts/verify-blocks.php','utf8');
  result.runtime=await page.evaluate(async code=>{
    const p=window.playground;
    const audit=(await p.run({code})).text;
    const log=await p.fileExists('/wordpress/wp-content/debug.log')?await p.readFileAsText('/wordpress/wp-content/debug.log'):'';
    return {audit:JSON.parse(audit),debugLog:log};
  },auditCode);
  result.noManualIntervention=true;
  await save(state);
  console.log({key:result.key,h1:result.initialH1,wp:result.runtime.audit.wp,php:result.runtime.audit.php,plugins:result.runtime.audit.plugins,errors:result.errors,resources:result.resources});
}
export async function save(state){
  await fs.mkdir(root+'/docs/qa/public',{recursive:true});
  await fs.writeFile(root+`/docs/qa/public/${state.result.key}.json`,JSON.stringify(state.result,null,2)+'\n');
}
export async function screenshots(state){
  const folder=root+'/docs/screenshots/public';
  await fs.mkdir(folder,{recursive:true});
  for(const [slug,path] of [['home','/'],['cena-stala','/oferta/cena-stala/']]){
    await state.page.evaluate(path=>window.playground.goTo(path),path);
    await state.frame.waitForURL(u=>u.pathname.endsWith(path));
    await state.frame.locator('#main h1').waitFor();
    for(const [device,width,height] of [['desktop',1440,900],['mobile',360,800]]){
      await state.page.setViewportSize({width,height});
      await state.frame.evaluate(()=>document.fonts.ready);
      await state.page.screenshot({path:`${folder}/${state.result.key}-${slug}-${device}.png`});
    }
  }
  state.result.productH1=await state.frame.locator('#main h1').innerText();
  await save(state);
}
export async function routes(state,from,to){
  const source=JSON.parse(await fs.readFile(root+'/docs/qa/p12-browser.json','utf8'));
  const routes=source.urls.slice(from,to).map(r=>({path:r.path,expected:r.expected}));
  const results=await state.page.evaluate(async routes=>{
    const out=[];
    for(const r of routes){
      let response=await window.playground.request({url:r.path,method:'GET'});
      const redirects=[];
      for(let n=0;n<4&&[301,302,303,307,308].includes(response.httpStatusCode);n++){
        const location=response.headers.location?.[0];
        if(!location)break;
        redirects.push({status:response.httpStatusCode,location});
        response=await window.playground.request({url:location,method:'GET'});
      }
      out.push({...r,redirects,status:response.httpStatusCode,h1:(response.text.match(/<h1\b/gi)||[]).length});
    }
    return out;
  },routes);
  state.result.routes=[...(state.result.routes||[]),...results];
  await save(state);
  console.log({checked:results.length,issues:results.filter(r=>r.status!==r.expected||r.h1!==1)});
}
