import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const root=new URL('..',import.meta.url).pathname.replace(/\/$/,'');
const base='https://raw.githubusercontent.com/ImaPolska/gaz-dla-przemyslu';
const ref='etap1-v0.1';
const blueprint=JSON.parse(execFileSync('git',['-C',root,'show',`${ref}:blueprints/main.json`],{encoding:'utf8'}));
function convert(value){
  if(Array.isArray(value))return value.map(convert);
  if(value&&typeof value==='object'){
    if(value.resource==='bundled')return {resource:'url',url:`${base}/${ref}/dist/main${value.path}`};
    return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,convert(v)]));
  }
  return value;
}
await fs.mkdir(`${root}/blueprints/public`,{recursive:true});
await fs.writeFile(`${root}/blueprints/public/main.json`,JSON.stringify(convert(blueprint),null,2)+'\n');
const urls={
  main:`https://playground.wordpress.net/?blueprint-url=${base}/etap1-v0.1-public/blueprints/public/main.json`,
};
for(const d of ['A','B','C']){
  urls[d]=`https://playground.wordpress.net/?blueprint-url=${base}/etap1-${d}/dist/etap1-${d}.zip`;
}
await fs.writeFile(`${root}/docs/playground-links.json`,JSON.stringify(urls,null,2)+'\n');
console.log(urls);
