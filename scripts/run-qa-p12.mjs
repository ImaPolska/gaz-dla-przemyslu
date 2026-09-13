import {chromium} from 'playwright';
import * as qa from './qa-p12.mjs';
import * as editor from './qa-editor-p12.mjs';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try {
  const state=await qa.start(browser);
  await qa.routes(state,0,100);
  for(const [slug,url,axe] of [
    ['home','/',true],['oferta','/oferta/',false],
    ['cena-stala','/oferta/cena-stala/',true],['ceny','/ceny-orientacyjne/',true],
    ['artykul','/wiedza/jak-zmienic-sprzedawce-gazu-w-firmie/',true],
  ]) await qa.views(state,slug,url,axe);
  await qa.interactions(state);
  const admin=await editor.session(browser,'admin','password');
  await editor.open(admin,16);
  await editor.serialization(admin);
} finally {
  await browser.close();
}
