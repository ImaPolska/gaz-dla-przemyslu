import fs from 'node:fs';
import path from 'node:path';
import Ajv from 'ajv';
const root = path.resolve(import.meta.dirname, '..');
const schema = JSON.parse(fs.readFileSync(path.join(root,'docs/qa/published-blueprint-schema.json')));
const ajv = new Ajv({strict:false,allErrors:true});
const validate = ajv.compile(schema);
const report = {};
for (const d of ['A','B','C']) {
  const bp = JSON.parse(fs.readFileSync(path.join(root,`blueprints/${d}.json`)));
  const valid = validate(bp);
  report[d] = {valid, errors:validate.errors, noPluginInstallSteps:!bp.steps.some(s=>s.step==='installPlugin'||s.step==='importWxr'), source:'https://playground.wordpress.net/blueprint-schema.json', fetched:'2026-09-13'};
  if (!valid) process.exitCode=1;
}
fs.mkdirSync(path.join(root,'docs/qa'),{recursive:true});
fs.writeFileSync(path.join(root,'docs/qa/schema.json'),JSON.stringify(report,null,2));
console.log(report);
