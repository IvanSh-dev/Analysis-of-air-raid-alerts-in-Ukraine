"""Point-in-time probabilities of any archive record over 1/3/7 local days."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from threadpoolctl import threadpool_limits
from .pipeline import ROOT,Vintages,local_midnight,check_fit_availability,EXCLUDED
from .improve import enrich,forecast,CONFIGS,NUMERIC,FOLDS

HORIZONS=(1,3,7)
DAY='2026-10-16'
PROB_FEATURES=NUMERIC+['positive7','positive28']

def add_presence(v,panel):
    parts=[]
    for day,g in panel.groupby('date',sort=True):
        g=g.copy();origin=local_midnight(day);t=v.before(origin)
        days=[(origin-pd.DateOffset(days=k)).strftime('%Y-%m-%d') for k in range(2,30)]
        history=v.frames[t].reindex(days)[list(g.region)].to_numpy(dtype=float)
        if not np.isfinite(history).all():
            raise ValueError('Missing presence history; not zero')
        g['positive7']=(history[:7]>0).mean(axis=0)
        g['positive28']=(history>0).mean(axis=0)
        for h in HORIZONS:
            windows=np.array([(history[k:k+h].sum(axis=0)>0) for k in range(29-h)])
            # Beta(1,1) smoothing keeps finite log-loss even for all-positive history.
            g[f'prior{h}']=(windows.sum(axis=0)+1)/(len(windows)+2)
        parts.append(g)
    return pd.concat(parts,ignore_index=True)

def period_panel(panel,horizon):
    parts=[]
    for region,g in panel.groupby('region'):
        g=g.sort_values('date').copy()
        windows=pd.concat([g.y.shift(-k) for k in range(horizon)],axis=1)
        g['count_total']=windows.sum(axis=1,min_count=horizon)
        g['period_end']=g.date.shift(-(horizon-1))
        g['label_available_at']=g.label_available_at.shift(-(horizon-1))
        g=g.dropna(subset=['count_total','period_end','label_available_at'])
        if len(g):
            expected=pd.to_datetime(g.date)+pd.Timedelta(days=horizon-1)
            if not expected.eq(pd.to_datetime(g.period_end)).all():
                raise ValueError('Non-contiguous target window')
        g['event']=(g.count_total>0).astype(int)
        g['horizon']=horizon
        parts.append(g)
    return pd.concat(parts,ignore_index=True)

def probability(train,frame,origin):
    check_fit_availability(train,origin)
    if train.event.nunique()==1:
        return np.full(len(frame),(train.event.sum()+1)/(len(train)+2))
    prep=ColumnTransformer([
        ('numeric',StandardScaler(),PROB_FEATURES),
        ('region',OneHotEncoder(handle_unknown='error',sparse_output=False),['region'])])
    model=make_pipeline(prep,LogisticRegression(C=.1,max_iter=1000,random_state=42))
    with threadpool_limits(limits=2):
        model.fit(train[PROB_FEATURES+['region']],train.event)
        return model.predict_proba(frame[PROB_FEATURES+['region']])[:,1]

def coherent_probabilities(predictions):
    """Non-learned cumulative maximum: P(any in 7d) >= P(any in 3d) >= P(any in 1d)."""
    p=predictions.copy()
    for model in ['prior','logistic']:
        wide=p.pivot(index=['date','region'],columns='horizon',values=model).reindex(columns=HORIZONS)
        if wide.isna().any().any():
            raise ValueError('Incomplete probability horizons')
        adjusted=pd.DataFrame(np.maximum.accumulate(wide.to_numpy(),axis=1),index=wide.index,columns=wide.columns)
        mapping=adjusted.stack().to_dict()
        p[model]=[mapping[(d,r,h)] for d,r,h in zip(p.date,p.region,p.horizon)]
    if not p[['prior','logistic']].ge(0).all().all() or not p[['prior','logistic']].le(1).all().all():
        raise ValueError('Invalid probability')
    return p

def probability_metrics(predictions,stage):
    rows=[]
    for (h,region),g in predictions.groupby(['horizon','region']):
        for model in ['prior','logistic']:
            p=g[model].clip(1e-8,1-1e-8);y=g.event
            rows.append({'stage':stage,'horizon':h,'region':region,'model':model,'n':len(g),
                'brier':float(((p-y)**2).mean()),
                'log_loss':float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean()),
                'observed_rate':float(y.mean()),'mean_probability':float(p.mean())})
    regional=pd.DataFrame(rows)
    macro=regional.groupby(['stage','horizon','model'])[['brier','log_loss','observed_rate','mean_probability']].mean().reset_index()
    return regional,macro

def choose_probability(macro):
    if set(macro.stage)!={'rolling_validation'}:
        raise ValueError('Probability selection requires rolling validation only')
    scores=macro.groupby('model').brier.mean()
    return 'logistic' if scores['logistic']<scores['prior'] else 'prior'

def count_forecast(train,frame,origin,h):
    # Fixed count-model configuration, not tuned on probability or test outcomes.
    train=train.copy();train['y']=train.count_total/h
    return forecast(CONFIGS['blend_7'],train,frame,origin)*h

def run(out):
    out.mkdir(parents=True,exist_ok=True)
    v=Vintages();panel=add_presence(v,enrich(v,v.panel()))
    panels={h:period_panel(panel,h) for h in HORIZONS}
    validation=[]
    for start,end in FOLDS:
        origin=local_midnight(start)
        # Same 67 forecast origins for all horizons; full 7-day outcomes fit in each fold.
        last_origin=(pd.Timestamp(end)-pd.Timedelta(days=6)).strftime('%Y-%m-%d')
        for h,data in panels.items():
            train=data[(data.date<start)&(pd.to_datetime(data.label_available_at,utc=True)<origin)]
            val=data[data.date.between(start,last_origin)].copy()
            check_fit_availability(val,local_midnight('2026-09-16'))
            p=val[['date','region','horizon','period_end','event','count_total','label_available_at','feature_available_at','origin']].copy()
            p['prior']=val[f'prior{h}'];p['logistic']=probability(train,val,origin)
            p['count_prediction']=count_forecast(train,val,origin,h)
            p['count_baseline']=val.mean7*h;p['fold']=start
            validation.append(p)
    validation=coherent_probabilities(pd.concat(validation,ignore_index=True))
    regional,macro=probability_metrics(validation,'rolling_validation')
    selected=choose_probability(macro)
    decision={'selected':selected,'criterion':'lowest validation macro Brier, equal horizon and region weights',
        'event':'at least one archive-recorded start in the entire selected local-day window',
        'horizons':HORIZONS,'fold_windows':FOLDS,'common_origins_per_region':67,
        'logistic_C':.1,'postprocessing':'cumulative maximum across 1,3,7 days; applied before scoring and inference',
        'independent_final_test':False,'count_model':'previously selected blend_7; refit for period-average count',
        'validation_macro':macro.to_dict('records')}
    (out/'selection.json').write_text(json.dumps(decision,indent=2)+'\n')
    validation.to_csv(out/'validation_predictions.csv',index=False)
    regional.to_csv(out/'metrics_by_region.csv',index=False)
    macro.to_csv(out/'metrics_macro.csv',index=False)
    reliability=[]
    for h,g in validation.groupby('horizon'):
        buckets=pd.cut(g[selected],bins=np.linspace(0,1,11),include_lowest=True)
        for bucket,b in g.groupby(buckets,observed=True):
            reliability.append({'horizon':h,'bin':str(bucket),'n':len(b),
                'mean_probability':float(b[selected].mean()),'observed_frequency':float(b.event.mean())})
    pd.DataFrame(reliability).to_csv(out/'reliability.csv',index=False)
    count_rows=[]
    for (h,region),g in validation.groupby(['horizon','region']):
        for model in ['count_baseline','count_prediction']:
            err=g[model]-g.count_total
            count_rows.append({'horizon':h,'region':region,'model':model,'mae':float(err.abs().mean()),
                'rmse':float(np.sqrt((err**2).mean())),'bias':float(err.mean())})
    counts=pd.DataFrame(count_rows)
    counts.to_csv(out/'count_metrics_by_region.csv',index=False)
    counts.groupby(['horizon','model'])[['mae','rmse','bias']].mean().reset_index().to_csv(out/'count_metrics_macro.csv',index=False)
    features=add_presence(v,enrich(v,v.feature_rows(DAY)))
    future=[]
    for h,data in panels.items():
        origin=local_midnight(DAY)
        train=data[pd.to_datetime(data.label_available_at,utc=True)<origin]
        p=features[['date','region','feature_available_at','feature_vintage']].copy()
        p['horizon']=h;p['period_end']=(pd.Timestamp(DAY)+pd.Timedelta(days=h-1)).strftime('%Y-%m-%d')
        p['prior']=features[f'prior{h}'];p['logistic']=probability(train,features,origin)
        p['count_prediction']=count_forecast(train,features,origin,h)
        p['count_baseline']=features.mean7*h
        future.append(p)
    future=coherent_probabilities(pd.concat(future,ignore_index=True))
    future['probability']=future[selected];future['probability_model']=selected
    missing=pd.DataFrame([{'date':DAY,'region':r,'horizon':h,
        'period_end':(pd.Timestamp(DAY)+pd.Timedelta(days=h-1)).strftime('%Y-%m-%d'),'status':reason}
        for r,reason in EXCLUDED.items() for h in HORIZONS])
    future['status']='archive-event estimate; not an official alert probability'
    pd.concat([future,missing],ignore_index=True).sort_values(['horizon','region']).to_csv(out/'forecasts.csv',index=False)
    verification={'regions':23,'horizons':list(HORIZONS),'validation_origins_per_region_per_horizon':67,
        'binary_probability_event':True,'probability_derived_from_count_distribution':False,
        'feature_origins_fixed_for_entire_window':True,'future_features_used':False,
        'later_publication_assumption':'Git commit plus 6 hours; actual first-publication time unverified',
        'unknown_regions_imputed':False,'new_independent_test':False}
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    # Latest known outcomes are descriptive diagnostics: this period was already exposed.
    # Predict all horizons first, including windows whose outcomes are not yet known;
    # retain missing labels and score only mature windows after coherent postprocessing.
    diagnostic=[]
    diagnostic_origin=local_midnight('2026-09-16')
    diag_features=panel[panel.date.between('2026-09-16','2026-10-13')]
    for h,data in panels.items():
        train=data[(data.date<'2026-09-16')&(pd.to_datetime(data.label_available_at,utc=True)<diagnostic_origin)]
        p=diag_features[['date','region']].merge(data[['date','region','event','count_total']],on=['date','region'],how='left')
        p['horizon']=h
        p['period_end']=(pd.to_datetime(p.date)+pd.Timedelta(days=h-1)).dt.strftime('%Y-%m-%d')
        p['prior']=diag_features[f'prior{h}'].to_numpy()
        p['logistic']=probability(train,diag_features,diagnostic_origin)
        p['count_prediction']=count_forecast(train,diag_features,diagnostic_origin,h)
        p['count_baseline']=diag_features.mean7.to_numpy()*h
        diagnostic.append(p)
    diagnostic=coherent_probabilities(pd.concat(diagnostic,ignore_index=True))
    known=diagnostic[diagnostic.event.notna()].copy()
    assert known.period_end.max()=='2026-10-13'
    reg,mac=probability_metrics(known,'exposed_diagnostic')
    diagnostic.to_csv(out/'diagnostic_predictions.csv',index=False)
    reg.to_csv(out/'diagnostic_by_region.csv',index=False)
    mac.to_csv(out/'diagnostic_macro.csv',index=False)
    bins=[]
    for h,g in known.groupby('horizon'):
        buckets=pd.cut(g[selected],bins=np.linspace(0,1,11),include_lowest=True)
        for bucket,b in g.groupby(buckets,observed=True):
            bins.append({'horizon':h,'bin':str(bucket),'n':len(b),
                'mean_probability':float(b[selected].mean()),'observed_frequency':float(b.event.mean())})
    pd.DataFrame(bins).to_csv(out/'diagnostic_reliability.csv',index=False)
    verification.update({'latest_exposed_diagnostic_scored':True,'latest_diagnostic_target_date':'2026-10-13',
        'unknown_diagnostic_windows_left_missing':int(len(diagnostic)-len(known))})
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(macro.to_string(index=False));print('Selected probability model:',selected)
    print('Already-exposed latest-outcome diagnostic:');print(mac.to_string(index=False))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'results/probability')
    run(p.parse_args().output)

if __name__=='__main__': main()
