const fs = await import('node:fs/promises');
const root=new URL('..',import.meta.url).pathname.replace(/\/$/,'');
const origin='http://127.0.0.1:9403';
export async function session(browser,user='redaktor',pass='GDP-prototyp-2026'){
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();
  await page.goto(origin+'/wp-login.php',{waitUntil:'networkidle'});
  await page.locator('#user_login').fill(user);
  await page.locator('#user_pass').fill(pass);
  await page.locator('#wp-submit').click();
  await page.waitForLoadState('networkidle');
  return {context,page,user,results:{}};
}
export async function open(state,id){
  await state.page.goto(origin+`/wp-admin/post.php?post=${id}&action=edit`,{waitUntil:'domcontentloaded'});
  await state.page.waitForFunction(()=>window.wp?.data?.select('core/editor')?.getCurrentPostId());
  await state.page.waitForFunction(()=>wp.data.select('core/block-editor').getBlocks().length>0);
  const welcome=state.page.getByRole('button',{name:'Close',exact:true});
  if(await welcome.count() && await welcome.first().isVisible())await welcome.first().click();
  await state.page.frameLocator('iframe[name="editor-canvas"]').locator('.block-editor-block-list__layout').first().waitFor();
}
export async function serialization(state){
  const report=await state.page.evaluate(async()=>{
    const items=[];
    for(const type of ['pages','posts','blocks']){
      const posts=await wp.apiFetch({path:`/wp/v2/${type}?context=edit&per_page=100`});
      for(const post of posts){
        const invalid=[];
        const walk=(blocks)=>{for(const b of blocks){if(!b.isValid)invalid.push({name:b.name,issues:b.validationIssues?.map(v=>v.args?.[0])});walk(b.innerBlocks||[]);}};
        walk(wp.blocks.parse(post.content.raw));
        items.push({id:post.id,type,slug:post.slug,invalid});
      }
    }
    const settings=wp.data.select('core/block-editor').getSettings();
    return {items,detailsBindings:settings.__experimentalBlockBindingsSupportedAttributes?.['core/details'],pass:items.every(i=>i.invalid.length===0)};
  });
  await fs.writeFile(root+'/docs/qa/p12-gutenberg.json',JSON.stringify(report,null,2));
  console.log({pass:report.pass,objects:report.items.length,invalid:report.items.filter(i=>i.invalid.length),detailsBindings:report.detailsBindings});
  return report;
}
export async function snapshot(state,filename){
  await fs.mkdir(root+'/docs/screenshots/p12/editor',{recursive:true});
  await state.page.screenshot({path:root+'/docs/screenshots/p12/editor/'+filename+'.png'});
}
export async function saveResult(value){
  await fs.writeFile(root+'/docs/qa/p12-editor.json',JSON.stringify(value,null,2));
}
