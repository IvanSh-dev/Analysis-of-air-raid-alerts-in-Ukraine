"""Bounded temporal model comparison; exposed test is diagnostic, never selection."""
import json
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from .pipeline import Vintages, ROOT, local_midnight, check_fit_availability, TEST

FOLDS = [('2026-06-15','2026-07-12'),('2026-07-15','2026-08-11'),('2026-08-15','2026-09-12')]
CONFIGS = {
    'baseline_7': {'kind':'mean7'}, 'median_7': {'kind':'median7'},
    'median_14': {'kind':'median14'}, 'ewm_7': {'kind':'ewm7'},
    'boost_7': {'kind':'boost','leaves':7,'blend':1.0},
    'boost_15': {'kind':'boost','leaves':15,'blend':1.0},
    'blend_7': {'kind':'boost','leaves':7,'blend':0.5},
    'blend_15': {'kind':'boost','leaves':15,'blend':0.5},
}
NUMERIC=['lag2','lag3','lag7','mean7','mean28','dow_sin','dow_cos','median7','median14','ewm7','trend','std7']

def enrich(v, frame):
    parts=[]
    for day,g in frame.groupby('date',sort=True):
        g=g.copy()
        origin=local_midnight(day)
        t=v.before(origin)
        dates=[(origin-pd.DateOffset(days=k)).strftime('%Y-%m-%d') for k in range(2,30)]
        history=v.frames[t].reindex(dates)[list(g.region)].to_numpy(dtype=float)
        if not np.isfinite(history).all():
            raise ValueError('Missing archive query in enhanced features')
        g['median7']=np.median(history[:7],axis=0)
        g['median14']=np.median(history[:14],axis=0)
        weights=0.75**np.arange(28)
        g['ewm7']=np.average(history,axis=0,weights=weights)
        g['trend']=g.mean7-g.mean28
        g['std7']=history[:7].std(axis=0)
        parts.append(g)
    return pd.concat(parts,ignore_index=True)

def inputs(frame):
    out=frame[NUMERIC+['region']].copy()
    out['region']=pd.Categorical(out.region)
    return out

def forecast(config,train,frame,origin):
    kind=config['kind']
    if kind!='boost':
        return frame[kind].to_numpy()
    check_fit_availability(train,origin)
    # Median-regression loss directly targets MAE; no random internal validation.
    model=HistGradientBoostingRegressor(loss='absolute_error',learning_rate=.05,
        max_iter=150,max_leaf_nodes=config['leaves'],min_samples_leaf=30,
        l2_regularization=1.,early_stopping=False,categorical_features=['region'],random_state=42)
    with threadpool_limits(limits=2):
        model.fit(inputs(train),train.y)
        pred=model.predict(inputs(frame))
    return np.maximum(0,config['blend']*pred+(1-config['blend'])*frame.mean7.to_numpy())

def score(pred):
    rows=[]
    for (model,region),g in pred.groupby(['model','region']):
        error=g.prediction-g.y
        rows.append(dict(model=model,region=region,n=len(g),mae=float(error.abs().mean()),
            rmse=float(np.sqrt(np.mean(error**2))),bias=float(error.mean())))
    regional=pd.DataFrame(rows)
    macro=regional.groupby('model')[['mae','rmse','bias']].mean().reset_index()
    return regional,macro

def choose(validation):
    if not validation['stage'].eq('rolling_validation').all():
        raise ValueError('Only rolling validation may select the model')
    return validation.sort_values(['mae','model'],kind='stable').iloc[0].model

def run(out):
    out.mkdir(parents=True,exist_ok=True)
    v=Vintages()
    panel=enrich(v,v.panel())
    all_predictions=[]
    for start,end in FOLDS:
        origin=local_midnight(start)
        train=panel[(panel.date<start)&(pd.to_datetime(panel.label_available_at,utc=True)<origin)]
        val=panel[panel.date.between(start,end)]
        assert val.groupby('region').size().nunique()==1
        for name,config in CONFIGS.items():
            p=val[['date','region','y']].copy()
            p['prediction']=forecast(config,train,val,origin)
            p['model']=name;p['fold']=start
            all_predictions.append(p)
    predictions=pd.concat(all_predictions,ignore_index=True)
    validation_days=set(predictions.date)
    check_fit_availability(panel[panel.date.isin(validation_days)],local_midnight(TEST[0]))
    regional,macro=score(predictions)
    macro['stage']='rolling_validation'
    selected=choose(macro)
    decision={'selected':selected,'criterion':'equal-region MAE on rolling validation only',
        'folds':FOLDS,'candidates':CONFIGS,'settings_fixed_before_run':True,
        'old_test_previously_seen':True,'fresh_independent_test_available':False,
        'selection_scores':macro.to_dict('records')}
    (out/'selection.json').write_text(json.dumps(decision,indent=2)+'\n')
    predictions.to_csv(out/'validation_predictions.csv',index=False)
    regional.to_csv(out/'validation_by_region.csv',index=False)
    macro.to_csv(out/'validation_macro.csv',index=False)
    fold_metrics=[]
    for fold,g in predictions.groupby('fold'):
        _,m=score(g);m['fold']=fold;fold_metrics.append(m)
    pd.concat(fold_metrics).to_csv(out/'validation_by_fold.csv',index=False)
    # This already-exposed period is a diagnostic, not a fresh unbiased final test.
    origin=local_midnight(TEST[0])
    train=panel[(panel.date<TEST[0])&(pd.to_datetime(panel.label_available_at,utc=True)<origin)]
    test=panel[panel.date.between(*TEST)]
    diagnostic=[]
    for name in dict.fromkeys(['baseline_7',selected]):
        p=test[['date','region','y']].copy()
        p['prediction']=forecast(CONFIGS[name],train,test,origin);p['model']=name
        diagnostic.append(p)
    diagnostic=pd.concat(diagnostic,ignore_index=True)
    r,m=score(diagnostic)
    diagnostic.to_csv(out/'diagnostic_predictions.csv',index=False)
    r.to_csv(out/'diagnostic_by_region.csv',index=False)
    m.to_csv(out/'diagnostic_macro.csv',index=False)
    day='2026-10-16'
    features=enrich(v,v.feature_rows(day))
    next_pred=forecast(CONFIGS[selected],panel,features,local_midnight(day))
    f=features[['date','region']].copy();f['forecast']=next_pred;f['baseline']=features.mean7
    f['selected_model']=selected
    f=f.merge(pd.read_csv(ROOT/'results/coverage.csv')[['region','status']],on='region',how='outer')
    f['date']=f.date.fillna(day)
    f.sort_values('region').to_csv(out/'next_day_forecast.csv',index=False)
    print(macro.sort_values('mae').to_string(index=False))
    print('Selected:',selected,'\nExposed-period diagnostic:\n',m.to_string(index=False))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'results/improved')
    run(p.parse_args().output)

if __name__=='__main__': main()
