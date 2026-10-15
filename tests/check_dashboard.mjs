// Logic/data checks with a minimal DOM fixture. This is NOT a browser/layout test.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html=fs.readFileSync(path.join(root,'site/index.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'site/data.json'),'utf8'));
class Element{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.attrs={};this.style={};this.dataset={};this.events={};this.value='';this._text='';this.hidden=false;}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[...nodes];this._text='';}
 setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k]??null;}
 addEventListener(k,f){this.events[k]=f;}
}
const ids=new Map();for(const match of html.matchAll(/\bid="([^"]+)"/g)){assert(!ids.has(match[1]),'Duplicate HTML id '+match[1]);ids.set(match[1],new Element());}
ids.get('sort').value='name';
const horizonButtons=[...html.matchAll(/data-horizon="(\d+)"/g)].map(m=>{const b=new Element('button');b.dataset.horizon=m[1];return b;});
const viewButtons=[...html.matchAll(/data-view="([^"]+)"/g)].map(m=>{const b=new Element('button');b.dataset.view=m[1];return b;});
const document={getElementById:id=>{assert(ids.has(id),'Missing HTML id '+id);return ids.get(id);},
 createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),
 querySelectorAll:q=>q==='[data-horizon]'?horizonButtons:q==='[data-view]'?viewButtons:[]};
vm.runInNewContext(fs.readFileSync(path.join(root,'site/app.js'),'utf8'),{document,window:{ALERT_DATA:data},Intl,console});
const click=e=>e.events.click({preventDefault(){}});
let checked=0;
for(const h of [1,3,7]){
 click(horizonButtons.find(b=>b.dataset.horizon===String(h)));
 assert(ids.get('period-range').textContent.includes(h===1?'16.10.2026':h===3?'18.10.2026':'22.10.2026'));
 assert.equal(ids.get('regions').children.length,27);
 const map=ids.get('map').children[0];assert.equal(map.children.filter(n=>n.tagName==='path').length,27);
 assert.equal(map.children.filter(n=>n.tagName==='circle').length,1);
 for(const region of data.regions){
  const button=ids.get('regions').children.find(b=>b.dataset.region===region.id);click(button);
  const p=region.periods[String(h)];assert.equal(ids.get('region-name').textContent,region.name);
  if(p.probability===null){assert.equal(ids.get('available-detail').hidden,true);assert.equal(ids.get('unavailable-detail').hidden,false);assert.equal(ids.get('map-value').textContent,'—');}
  else{assert.equal(ids.get('available-detail').hidden,false);assert.match(ids.get('forecast').textContent,/%$/);assert.equal(ids.get('chart').children[0].tagName,'svg');assert(!ids.get('forecast').textContent.includes('NaN'));}
  checked++;
 }
}
click(viewButtons.find(b=>b.dataset.view==='count'));assert(ids.get('map-heading').textContent.includes('Кількість'));
ids.get('search').value='Закар';ids.get('search').events.input();assert.equal(ids.get('regions').children.length,1);click(ids.get('regions').children[0]);assert.equal(ids.get('unavailable-detail').hidden,false);
ids.get('search').value='Atlantis';ids.get('search').events.input();assert(ids.get('regions').textContent.includes('не знайдено'));
click(ids.get('tab-diag'));assert.equal(ids.get('model-bars').children[0].tagName,'table');
ids.get('search').value='Київ';ids.get('search').events.input();click(ids.get('regions').children.find(b=>b.dataset.region==='Kyiv City'));
ids.get('evaluation-stage').value='diagnostic';ids.get('evaluation-stage').events.change();
assert(ids.get('history-note').textContent.includes('не незалежний тест'));
assert(ids.get('history-range').textContent.includes('07.10'));
assert(ids.get('metric-description').textContent.includes('раніше переглянутий'));
assert(ids.get('chart').children[0].getAttribute('aria-label').includes('раніше переглянутий'));
assert(html.includes('https://t.me/air_alert_atlas_bot'));
assert(!html.includes('Бот ще не зареєстрований'));
assert(!html.includes('bot123')&&!html.includes('TELEGRAM_BOT_TOKEN'));
console.log(JSON.stringify({region_horizon_states_checked:checked,map_shapes:27,capital_marker:1,missing_not_zero:true,html_ids_unique:true,check_type:'minimal DOM logic checks; not browser/layout QA'},null,2));
