import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..');
const runtime=process.argv[2];
if(!runtime)throw new Error('Pass the local Playground WordPress directory');
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const browser=await read('docs/qa/p12-browser.json');
const editor=await read('docs/qa/p12-editor.json');
const gutenberg=await read('docs/qa/p12-gutenberg.json');
const build=await read('content/build-report.json');
const placeholders=await read('docs/qa/open-items.json');
async function files(dir){
  const out=[];
  for(const e of await fs.readdir(dir,{withFileTypes:true})){
    const p=path.join(dir,e.name);out.push(...e.isDirectory()?await files(p):[p]);
  }return out;
}
const canonical=(await files(path.join(root,'content'))).filter(p=>p.endsWith('.html'));
const textIssues=[],tables=[];
for(const file of canonical){
  const content=await fs.readFile(file,'utf8'),name=path.relative(root,file);
  const text=content.replace(/<[^>]*>/g,' ');
  for(const phrase of ['w dzisiejszych czasach','kompleksowe rozwiązania','lider rynku','innowacyjny','game-changer']){
    if(text.toLowerCase().includes(phrase))textIssues.push({file:name,phrase});
  }
  if(/\sstyle\s*=/i.test(content))textIssues.push({file:name,issue:'inline-style'});
  for(const table of content.matchAll(/<table\b[\s\S]*?<\/table>/g))tables.push({file:name,thead:/<thead\b/.test(table[0])});
}
const sourceTheme=path.join(root,'theme/gdp-child'),themeIssues=[];
const sourceFiles=await files(sourceTheme);
for(const f of sourceFiles){
  const rel=path.relative(sourceTheme,f);
  try{
    const a=await fs.readFile(f),b=await fs.readFile(path.join(runtime,'wp-content/themes/gdp-child',rel));
    if(!a.equals(b))themeIssues.push(rel);
  }catch{themeIssues.push(rel);}
}
const debugPath=path.join(runtime,'wp-content/debug.log');
let log='',logExists=false;
try{log=await fs.readFile(debugPath,'utf8');logExists=true;}catch(e){if(e.code!=='ENOENT')throw e;}
const bundle=await fs.readFile(path.join(root,'dist/etap1-v0.1.zip'));
const sha=createHash('sha256').update(bundle).digest('hex');
const report={
  timestamp:new Date().toISOString(),scope:'Local Playground only; public repository and Playground URL not delivered',
  bundle_sha256:sha,
  objects:Object.fromEntries(['page','post','wp_block'].map(t=>[t,build.items.filter(i=>i.post_type===t).length])),
  routes:{count:browser.urls.length,failures:browser.urls.filter(r=>r.status!==r.expected||r.h1!==1||r.overflow||r.headingJumps?.length)},
  blocks:browser.audit.counts,sectionExceptions:browser.audit.documented_exceptions,
  schema:await read('docs/qa/schema-p12.json'),
  environment:{wp:browser.audit.wp,php:browser.audit.php,parent:browser.audit.parent,parentVersion:browser.audit.parent_version,child:browser.audit.stylesheet,plugins:browser.audit.plugins,paletteMatches:browser.audit.palette_matches},
  php:{debug:browser.audit.debug,logExists,bytes:Buffer.byteLength(log),noticesOrWarnings:(log.match(/(?:Warning|Notice|Fatal error|Parse error)/g)||[]).length},
  themeReproduction:{checkedFiles:sourceFiles.length,mismatches:themeIssues},
  axe:browser.axe.map(a=>({path:a.path,violations:a.violations.length,incomplete:a.incomplete.length})),
  responsive:{views:browser.views.length,issues:browser.views.filter(v=>v.width!==v.scrollWidth||!v.ctaAboveFold||v.smallText.length)},
  hosts:browser.hosts,jsErrors:browser.errors,failedRequests:browser.failedRequests,
  content:{placeholders:placeholders.count,issues:textIssues,tables:tables.length,tablesWithoutHead:tables.filter(t=>!t.thead)},
  serialization:{objects:gutenberg.items.length,pass:gutenberg.pass,invalid:gutenberg.items.filter(i=>i.invalid.length)},
  editing:{hero:editor.hero,restGuard:editor.restGuard,article:editor.article,admin:editor.admin,overrides:editor.overrides,propagation:editor.propagation,starter:editor.starter},
};
report.localPass=report.routes.failures.length===0&&!Object.values(report.blocks).some(Boolean)&&!themeIssues.length&&
  !report.php.noticesOrWarnings&&report.axe.every(a=>a.violations===0)&&!report.responsive.issues.length&&
  !report.jsErrors.length&&!report.failedRequests.length&&!textIssues.length&&!report.content.tablesWithoutHead.length&&gutenberg.pass;
report.completeP12Delivery=false;
await fs.writeFile(path.join(root,'docs/qa/p12-final.json'),JSON.stringify(report,null,2)+'\n');
console.log({localPass:report.localPass,completeP12Delivery:false,objects:report.objects,routes:report.routes.count,theme:report.themeReproduction,php:report.php,bundle_sha256:sha});
