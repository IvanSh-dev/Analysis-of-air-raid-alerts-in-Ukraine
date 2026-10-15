"""Export checked probabilities, period counts and real map shapes, offline."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from alerts_forecast.regions import LABELS,ISOS,REGISTRY

def map_data():
    raw=(ROOT/'data/ukraine_adm1.geojson').read_bytes()
    source=json.loads((ROOT/'data/geometry_source.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=source['download_sha256']:
        raise ValueError('Geometry checksum mismatch')
    features=json.loads(raw)['features']
    if {x['properties']['shapeISO'] for x in features}!={r[0] for r in REGISTRY}:
        raise ValueError('Map does not match all 27 registered territories')
    def rings(geometry):
        if geometry['type']=='Polygon':return geometry['coordinates']
        if geometry['type']=='MultiPolygon':return [ring for polygon in geometry['coordinates'] for ring in polygon]
        raise ValueError('Unexpected geometry type')
    points=[p for f in features for ring in rings(f['geometry']) for p in ring]
    lon_scale=math.cos(math.radians(49))
    xmin=min(p[0]*lon_scale for p in points);xmax=max(p[0]*lon_scale for p in points)
    ymin=min(p[1] for p in points);ymax=max(p[1] for p in points)
    width=900;height=(ymax-ymin)/(xmax-xmin)*width
    def project(p):return ((p[0]*lon_scale-xmin)/(xmax-xmin)*width,(ymax-p[1])/(ymax-ymin)*height)
    shapes=[]
    for f in features:
        rr=rings(f['geometry']);parts=[];xy=[]
        for ring in rr:
            pts=[project(p) for p in ring];xy.extend(pts)
            parts.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'Z')
        shapes.append({'iso':f['properties']['shapeISO'],'path':''.join(parts),
            'center':[(min(p[0] for p in xy)+max(p[0] for p in xy))/2,
                      (min(p[1] for p in xy)+max(p[1] for p in xy))/2]})
    return {'viewBox':f'-10 -10 {width+20:.2f} {height+20:.2f}','shapes':shapes,
        'attribution':'© OpenStreetMap contributors · geoBoundaries · ODbL 1.0',
        'source':'https://www.geoboundaries.org/api/current/gbOpen/UKR/ADM1/','year':2017}

def main():
    result=ROOT/'results/probability'
    forecast=pd.read_csv(result/'forecasts.csv')
    coverage=pd.read_csv(ROOT/'results/coverage.csv')
    pred=pd.read_csv(result/'validation_predictions.csv')
    selection=json.loads((result/'selection.json').read_text())
    regional=pd.read_csv(result/'metrics_by_region.csv')
    diagnostic=pd.read_csv(result/'diagnostic_predictions.csv').dropna(subset=['event'])
    regions=[];selected=selection['selected']
    for iso,name,uk in REGISTRY:
        cov=coverage[coverage.region.eq(name)].iloc[0]
        entry={'id':name,'iso':iso,'name':uk,'last':None if pd.isna(cov.last_observed_start_utc) else cov.last_observed_start_utc,
            'reason':'Дані архіву застаріли' if name in ['Luhanska oblast','Zakarpatska oblast'] else 'Територія відсутня у джерелі','periods':{}}
        for h in [1,3,7]:
            row=forecast[(forecast.region.eq(name))&(forecast.horizon.eq(h))].iloc[0]
            if pd.isna(row.probability):
                entry['periods'][str(h)]={'probability':None,'count':None,'baselineProbability':None,'countBaseline':None,'history':[],'brier':None,'end':row.period_end}
                continue
            history=pred[(pred.region.eq(name))&(pred.horizon.eq(h))&(pred.fold.eq('2026-08-15'))]
            metric=regional[(regional.region.eq(name))&(regional.horizon.eq(h))&(regional.model.eq(selected))].iloc[0]
            entry['periods'][str(h)]={'probability':float(row.probability),'baselineProbability':float(row.prior),
                'count':float(row.count_prediction),'countBaseline':float(row.count_baseline),'end':row.period_end,
                'brier':float(metric.brier),'history':[{'date':r.date,'end':r.period_end,'actual':int(r.event),
                    'probability':float(getattr(r,selected)),'baseline':float(r.prior),
                    'countActual':int(r.count_total),'count':float(r.count_prediction),'countBaseline':float(r.count_baseline)} for r in history.itertuples()]}
            recent=diagnostic[(diagnostic.region.eq(name))&(diagnostic.horizon.eq(h))]
            entry['periods'][str(h)]['diagnosticHistory']=[{'date':r.date,'end':r.period_end,'actual':int(r.event),
                'probability':float(getattr(r,selected)),'baseline':float(r.prior),'countActual':int(r.count_total),
                'count':float(r.count_prediction),'countBaseline':float(r.count_baseline)} for r in recent.itertuples()]
        regions.append(entry)
    payload={'schemaVersion':3,'forecastDate':'2026-10-16','dataVersion':'2026-10-15','lastTarget':'2026-10-13',
        'selected':selected,'regions':regions,'metrics':pd.read_csv(result/'metrics_macro.csv').to_dict('records'),
        'countMetrics':pd.read_csv(result/'count_metrics_macro.csv').to_dict('records'),
        'reliability':pd.read_csv(result/'reliability.csv').to_dict('records'),
        'diagnosticMetrics':pd.read_csv(result/'diagnostic_macro.csv').to_dict('records'),
        'diagnosticReliability':pd.read_csv(result/'diagnostic_reliability.csv').to_dict('records'),
        'event':'at least one archive-recorded start in selected window','map':map_data()}
    assert len(regions)==27
    assert all(sum(r['periods'][str(h)]['probability'] is not None for r in regions)==23 for h in [1,3,7])
    raw=json.dumps(payload,ensure_ascii=False,allow_nan=False)
    site=ROOT/'site';site.mkdir(exist_ok=True)
    (site/'data.js').write_text('window.ALERT_DATA = '+raw+';\n',encoding='utf-8')
    (site/'data.json').write_text(raw+'\n',encoding='utf-8')
    shutil.copy2(result/'forecasts.csv',site/'forecasts.csv')
    print('Dashboard: checked 27 shapes, 23 forecasts per horizon, periods 1/3/7, binary-event probabilities.')

if __name__=='__main__':main()
