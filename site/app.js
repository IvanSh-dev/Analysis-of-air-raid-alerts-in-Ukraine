'use strict';
const data=window.ALERT_DATA,$=id=>document.getElementById(id);
const fmt=(v,d=2)=>new Intl.NumberFormat('uk-UA',{maximumFractionDigits:d,minimumFractionDigits:d}).format(v);
const pct=p=>p===null?'—':p>.999?'>99,9%':p<.001?'<0,1%':fmt(p*100,1)+'%';
const date=d=>d.slice(8)+'.'+d.slice(5,7)+'.'+d.slice(0,4);
let selected='Kyiv City',horizon=1,view='probability',metricMode='error',evaluationStage='validation';
const current=r=>r.periods[String(horizon)];
const scalar=p=>view==='probability'?p.probability:p.count;
function pick(id){selected=id;renderList();renderDetail();renderMap();}
function update(){
 const end=data.regions[0].periods[String(horizon)].end;
 $('period-range').textContent=date(data.forecastDate)+(end===data.forecastDate?'':' — '+date(end));
 $('detail-period').textContent=horizon===1?'1 календарний день':horizon===3?'3 календарні дні':'7 календарних днів';
 document.querySelectorAll('[data-horizon]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.horizon)===horizon)));
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
 const score=data.metrics.find(r=>r.horizon===horizon&&r.model===data.selected),base=data.metrics.find(r=>r.horizon===horizon&&r.model==='prior');
 $('cv-mae').textContent=fmt(score.brier,4);const change=(score.brier/base.brier-1)*100;
 $('gain').textContent=(change>0?'+':'')+fmt(change,1)+'%';$('gain').className=change<=0?'green':'worse';
 $('gain-caption').textContent=change>0?'на цьому горизонті базовий трохи кращий':'нижча похибка за базову частоту';
 $('observed-rate').textContent=pct(score.observed_rate);
 renderList();renderDetail();renderMap();renderMetrics();
}
function renderList(){
 const q=$('search').value.trim().toLocaleLowerCase('uk');const rows=data.regions.filter(r=>r.name.toLocaleLowerCase('uk').includes(q));
 rows.sort((a,b)=>$('sort').value==='forecast'?(scalar(current(b))??-1)-(scalar(current(a))??-1):a.name.localeCompare(b.name,'uk'));
 $('regions').replaceChildren();$('region-count').textContent=`${rows.length} із 27 територій`;
 if(!rows.length){const p=document.createElement('p');p.textContent='Регіонів не знайдено';p.className='empty-search';$('regions').append(p);}
 for(const r of rows){const p=current(r),button=document.createElement('button');button.className='region-row'+(p.probability===null?' unavailable':'');button.dataset.region=r.id;button.setAttribute('aria-pressed',String(r.id===selected));
 const name=document.createElement('span');name.textContent=r.name;const value=document.createElement('strong');value.textContent=view==='probability'?pct(p.probability):p.count===null?'—':fmt(p.count,1);button.append(name,value);button.addEventListener('click',()=>pick(r.id));$('regions').append(button);}
}
function renderDetail(){
 const r=data.regions.find(r=>r.id===selected),p=current(r),available=p.probability!==null;
 $('region-name').textContent=r.name;$('availability').textContent=available?'Оцінка архівної події':'Немає даних';$('availability').className='badge'+(available?'':' missing');
 $('available-detail').hidden=!available;$('unavailable-detail').hidden=available;$('last-record').textContent=r.last?r.last.replace('+00:00',''):'немає';
 if(!available){$('unavailable-reason').textContent=r.reason;return;}
 $('forecast').textContent=pct(p.probability);$('baseline').textContent=pct(p.baselineProbability);
 $('count-forecast').textContent=fmt(p.count,1)+' записів';$('count-baseline').textContent=fmt(p.countBaseline,1)+' записів';
 $('region-mae').textContent=fmt(p.brier,4);$('chart-heading').textContent=view==='probability'?'Ймовірність і спостереження':'Кількість записів за вибране вікно';
 const recent=evaluationStage==='diagnostic',history=recent?p.diagnosticHistory:p.history;
 $('actual-label').textContent=view==='probability'?'Подія: 0% або 100%':'Фактичні записи';
 $('history-range').textContent='Початки: '+history[0].date.slice(8)+'.'+history[0].date.slice(5,7)+' — '+history.at(-1).date.slice(8)+'.'+history.at(-1).date.slice(5,7);
 $('history-note').textContent=recent?'Раніше переглянутий період; не незалежний тест.':'Графік: останній відрізок; Brier: усі 67 початків. Вікна 3/7 днів перекриваються.';
 $('region-score-label').textContent=recent?'Brier цього періоду:':'Brier усієї валідації:';
 if(recent)$('region-mae').textContent=fmt(history.reduce((s,d)=>s+(d.probability-d.actual)**2,0)/history.length,4);
 drawChart(r,{...p,history});
}
function renderMap(){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',data.map.viewBox);svg.setAttribute('role','group');svg.setAttribute('aria-label','Карта прогнозів України');
 const defs=document.createElementNS(ns,'defs');defs.innerHTML='<pattern id="missing-hatch" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#e9eae3"/><path d="M0 7L7 0" stroke="#b9bfb1" stroke-width="1"/></pattern>';svg.append(defs);
 const max=view==='probability'?1:Math.max(...data.regions.map(r=>current(r).count??0));
 function attach(node,r){const p=current(r),value=scalar(p),t=value===null?null:Math.max(0,Math.min(1,value/max));
 node.setAttribute('fill',t===null?'url(#missing-hatch)':`rgb(${Math.round(235-192*t)},${Math.round(242-142*t)},${Math.round(211-155*t)})`);node.setAttribute('class','map-path'+(r.id===selected?' selected':''));node.setAttribute('role','button');node.setAttribute('tabindex','0');node.dataset.region=r.id;
 const label=r.name+': '+(p.probability===null?'немає даних':pct(p.probability)+', '+fmt(p.count,1)+' записів');node.setAttribute('aria-label',label);node.setAttribute('aria-pressed',String(r.id===selected));
 const title=document.createElementNS(ns,'title');title.textContent=label;node.append(title);node.addEventListener('click',()=>pick(r.id));node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick(r.id);}});}
 for(const shape of data.map.shapes){const r=data.regions.find(x=>x.iso===shape.iso);const path=document.createElementNS(ns,'path');path.setAttribute('d',shape.path);path.setAttribute('fill-rule','evenodd');attach(path,r);svg.append(path);}
 const capital=data.map.shapes.find(s=>s.iso==='UA-30'),circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',capital.center[0]);circle.setAttribute('cy',capital.center[1]);circle.setAttribute('r',8);attach(circle,data.regions.find(r=>r.iso==='UA-30'));circle.setAttribute('aria-label','м. Київ: '+pct(current(data.regions.find(r=>r.iso==='UA-30')).probability));svg.append(circle);
 $('map').replaceChildren(svg);const r=data.regions.find(x=>x.id===selected),p=current(r);
 $('map-heading').textContent=view==='probability'?'Ймовірність на карті':'Кількість записів на карті';$('map-region').textContent=r.name;
 $('map-value').textContent=view==='probability'?pct(p.probability):p.count===null?'—':fmt(p.count,1);
 $('map-detail').textContent=p.probability===null?r.reason:view==='probability'?`Хоча б один запис за ${horizon} ${horizon===1?'день':horizon===3?'дні':'днів'}. Це не оцінка небезпеки.`:`Прогнозована кількість записів за весь період ${date(data.forecastDate)}–${date(p.end)}.`;
 $('scale-min').textContent=view==='probability'?'0%':'0';$('scale-max').textContent=view==='probability'?'100%':fmt(max,1);
}
function drawChart(r,p){
 const rows=p.history,W=750,H=240,L=34,R=12,T=18,B=32;const prob=view==='probability';
 const actual=d=>prob?d.actual:d.countActual,estimate=d=>prob?d.probability:d.count,baseline=d=>prob?d.baseline:d.countBaseline;
 const top=prob?1:Math.max(2,...rows.flatMap(d=>[actual(d),estimate(d),baseline(d)]));const max=prob?1:Math.ceil(top/4)*4;
 const x=i=>L+i*(W-L-R)/(rows.length-1),y=v=>T+(1-v/max)*(H-T-B),ns='http://www.w3.org/2000/svg';
 const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',`${r.name}: ${prob?'ймовірності':'кількість'}, період ${horizon} днів, часова валідація`);
 const add=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n;};
 for(let i=0;i<=4;i++){const v=max*i/4;add('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),stroke:'#e9ede4','stroke-dasharray':'3 4'});add('text',{x:L-7,y:y(v)+4,'text-anchor':'end',fill:'#78816f','font-size':10},prob?Math.round(v*100)+'%':fmt(v,0));}
 for(const i of [0,7,14,rows.length-1])add('text',{x:x(i),y:H-10,'text-anchor':i===0?'start':i===rows.length-1?'end':'middle',fill:'#78816f','font-size':10},rows[i].date.slice(8)+'.'+rows[i].date.slice(5,7));
 for(const [fn,color,dash]of [[baseline,'#bb794a','5 4'],[estimate,'#749d3c','none']])add('polyline',{points:rows.map((d,i)=>`${x(i)},${y(fn(d))}`).join(' '),fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':dash});
 if(!prob)add('polyline',{points:rows.map((d,i)=>`${x(i)},${y(actual(d))}`).join(' '),fill:'none',stroke:'#233932','stroke-width':2});
 rows.forEach((d,i)=>{const n=add('circle',{cx:x(i),cy:y(actual(d)),r:3.5,fill:'#233932',tabindex:0});const title=document.createElementNS(ns,'title');title.textContent=`${d.date}–${d.end}\nПодія: ${d.actual}\nЙмовірність: ${pct(d.probability)}\nЗаписів: ${d.countActual}\nПрогноз кількості: ${fmt(d.count,1)}`;n.append(title);});$('chart').replaceChildren(svg);
}
function renderMetrics(){
 const error=metricMode==='error';$('tab-val').setAttribute('aria-selected',String(error));$('tab-diag').setAttribute('aria-selected',String(!error));$('model-bars').replaceChildren();
 const source=evaluationStage==='diagnostic'?data.diagnosticMetrics:data.metrics;
 if(error){const scores=source.filter(r=>r.horizon===horizon).sort((a,b)=>a.brier-b.brier),max=Math.max(...scores.map(s=>s.brier))*1.15;
 $('metric-description').textContent=evaluationStage==='diagnostic'?`Раніше переглянутий період: результати відомі до 13.10.2026 включно. Для ${horizon} днів — ${29-horizon} початків на регіон. Це не новий незалежний тест і не підбір моделі.`:`Період ${horizon} днів. Три часові відрізки, 67 початків прогнозу на регіон. Глобальний вибір зроблено за середнім Brier горизонтів 1/3/7.`;
 for(const s of scores){const row=document.createElement('div');row.className='metric-bar-row';const name=document.createElement('span');name.textContent=s.model==='prior'?'Історична частота':'Логістична регресія';const track=document.createElement('div');track.className='bar-track';const fill=document.createElement('div');fill.className='bar-fill'+(s.model===data.selected?' selected':'');fill.style.width=(s.brier/max*100)+'%';track.append(fill);const value=document.createElement('strong');value.textContent=fmt(s.brier,4);row.append(name,track,value);$('model-bars').append(row);const loss=document.createElement('p');loss.className='loss-note';loss.textContent=`Log loss: ${fmt(s.log_loss,4)} · середній прогноз: ${pct(s.mean_probability)}`;$('model-bars').append(loss);}}
 else{$('metric-description').textContent=`Калібрування: ${evaluationStage==='diagnostic'?'раніше переглянутий період':'часова валідація'}, ${horizon} днів. Порівнюємо середню ймовірність зі спостереженою частотою. Малі групи нестійкі.`;
 const table=document.createElement('table');table.className='calibration-table';const head=document.createElement('tr');for(const name of ['Прогноз','Факт','Вікон']){const th=document.createElement('th');th.textContent=name;head.append(th);}table.append(head);
 const reliability=evaluationStage==='diagnostic'?data.diagnosticReliability:data.reliability;
 for(const bin of reliability.filter(r=>r.horizon===horizon)){const tr=document.createElement('tr');for(const value of [pct(bin.mean_probability),pct(bin.observed_frequency),String(bin.n)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}table.append(tr);}$('model-bars').append(table);}
}
document.querySelectorAll('[data-horizon]').forEach(b=>b.addEventListener('click',()=>{horizon=Number(b.dataset.horizon);update();}));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;update();}));
$('search').addEventListener('input',renderList);$('sort').addEventListener('change',renderList);
$('evaluation-stage').addEventListener('change',()=>{evaluationStage=$('evaluation-stage').value;renderDetail();renderMetrics();});
$('tab-val').addEventListener('click',()=>{metricMode='error';renderMetrics();});$('tab-diag').addEventListener('click',()=>{metricMode='calibration';renderMetrics();});update();
