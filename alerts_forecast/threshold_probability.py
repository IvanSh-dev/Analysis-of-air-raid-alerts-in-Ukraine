"""Separate >=3-per-day probability experiment and diagnostic baseline checks."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits
from .pipeline import ROOT, Vintages, EXCLUDED, local_midnight, check_fit_availability
from .improve import FOLDS, enrich
from .periods import (HORIZONS, DAY, PROB_FEATURES, add_presence, period_panel,
                      coherent_probabilities, choose_probability)
from .diagnose_threshold import window_labels

FEATURES = PROB_FEATURES + ['ge3_7', 'ge3_28']
MODELS = ['prior', 'logistic', 'train_majority', 'train_frequency', 'always_one', 'always_zero']


def add_threshold_presence(vintages, panel):
    parts = []
    for day, group in panel.groupby('date', sort=True):
        group = group.copy()
        origin = local_midnight(day)
        vintage = vintages.before(origin)
        days = [(origin-pd.DateOffset(days=k)).strftime('%Y-%m-%d') for k in range(2, 30)]
        history = vintages.frames[vintage].reindex(days)[list(group.region)].to_numpy(dtype=float)
        if not np.isfinite(history).all():
            raise ValueError('Missing threshold history is not zero')
        events = history >= 3
        group['ge3_7'] = events[:7].mean(axis=0)
        group['ge3_28'] = events.mean(axis=0)
        for horizon in HORIZONS:
            windows = np.array([events[k:k+horizon].any(axis=0) for k in range(29-horizon)])
            group[f'prior{horizon}'] = (windows.sum(axis=0)+1)/(len(windows)+2)
        parts.append(group)
    return pd.concat(parts, ignore_index=True)


def threshold_panel(panel, horizon):
    result = period_panel(panel, horizon)
    labels = window_labels(panel, horizon)
    result = result.merge(labels[['date', 'region', 'event_ge3']], on=['date', 'region'], validate='one_to_one')
    if result.event_ge3.isna().any():
        raise ValueError('Threshold target must be complete before training/scoring')
    result['event'] = result.pop('event_ge3').astype(int)
    return result


def predict_probability(train, frame, origin):
    check_fit_availability(train, origin)
    if train.event.nunique() == 1:
        return np.full(len(frame), (train.event.sum()+1)/(len(train)+2))
    prep = ColumnTransformer([
        ('numeric', StandardScaler(), FEATURES),
        ('region', OneHotEncoder(handle_unknown='error', sparse_output=False), ['region'])])
    model = make_pipeline(prep, LogisticRegression(C=.1, max_iter=1000, random_state=42))
    with threadpool_limits(limits=2):
        model.fit(train[FEATURES+['region']], train.event)
        return model.predict_proba(frame[FEATURES+['region']])[:, 1]


def fixed_baselines(train, frame, origin):
    """Regional frequencies/classes learned from eligible training labels only."""
    check_fit_availability(train, origin)
    rates = train.groupby('region').event.mean()
    frequency = frame.region.map(rates)
    if frequency.isna().any():
        raise ValueError('No eligible training labels for a requested region')
    return {'train_frequency': frequency.to_numpy(),
            'train_majority': frequency.ge(.5).astype(int).to_numpy(),
            'always_one': np.ones(len(frame)), 'always_zero': np.zeros(len(frame))}


def scores(predictions, stage):
    rows = []
    known = predictions.dropna(subset=['event'])
    for (horizon, region), group in known.groupby(['horizon', 'region']):
        y = group.event.to_numpy()
        variable = np.unique(y).size == 2
        for name in MODELS:
            raw = group[name].to_numpy()
            if not np.isfinite(raw).all() or not ((raw >= 0) & (raw <= 1)).all():
                raise ValueError('Invalid probability')
            clipped = np.clip(raw, 1e-8, 1-1e-8)
            rows.append({'stage': stage, 'horizon': horizon, 'region': region, 'model': name,
                         'n': len(y), 'brier': float(np.mean((raw-y)**2)),
                         'log_loss': float(-np.mean(y*np.log(clipped)+(1-y)*np.log(1-clipped))),
                         'observed_rate': float(y.mean()), 'mean_probability': float(raw.mean()),
                         'roc_auc': float(roc_auc_score(y, raw)) if variable else np.nan,
                         'auc_defined': variable})
    regional = pd.DataFrame(rows)
    macro = regional.groupby(['stage', 'horizon', 'model']).agg(
        brier=('brier', 'mean'), log_loss=('log_loss', 'mean'),
        observed_rate=('observed_rate', 'mean'), mean_probability=('mean_probability', 'mean'),
        roc_auc=('roc_auc', 'mean'), auc_regions=('auc_defined', 'sum'), regions=('region', 'nunique')).reset_index()
    return regional, macro


def append_baselines(predictions, panels):
    """Attach frozen fold-specific references to existing prediction rows."""
    chunks = []
    grouping = predictions.groupby('fold') if 'fold' in predictions else [('2026-09-16', predictions)]
    for start, fold in grouping:
        origin = local_midnight(start)
        for horizon, group in fold.groupby('horizon'):
            data = panels[int(horizon)]
            train = data[(data.date < start) & (pd.to_datetime(data.label_available_at, utc=True) < origin)]
            group = group.copy()
            for name, values in fixed_baselines(train, group, origin).items():
                group[name] = values
            chunks.append(group)
    return pd.concat(chunks, ignore_index=True)


def reliability(predictions, selected):
    rows = []
    for horizon, group in predictions.dropna(subset=['event']).groupby('horizon'):
        buckets = pd.cut(group[selected], np.linspace(0, 1, 11), include_lowest=True)
        for bucket, chunk in group.groupby(buckets, observed=True):
            rows.append({'horizon': horizon, 'bin': str(bucket), 'n': len(chunk),
                         'mean_probability': float(chunk[selected].mean()),
                         'observed_frequency': float(chunk.event.mean())})
    return pd.DataFrame(rows)


def write_evaluation(predictions, out, diagnostic=False):
    stage = 'exposed_diagnostic' if diagnostic else 'rolling_validation'
    regional, macro = scores(predictions, stage)
    prefix = 'diagnostic' if diagnostic else 'metrics'
    regional.to_csv(out/f'{prefix}_by_region.csv', index=False)
    macro.to_csv(out/f'{prefix}_macro.csv', index=False)
    predictions.to_csv(out/('diagnostic_predictions.csv' if diagnostic else 'validation_predictions.csv'), index=False)
    return macro


def run(out, comparison_out):
    out, comparison_out = out.resolve(), comparison_out.resolve()
    if out == comparison_out or out == ROOT/'results' or comparison_out == ROOT/'results':
        raise ValueError('Separate output directories are required')
    for destination in [out, comparison_out]:
        for original in [ROOT/'results/probability', ROOT/'results/improved']:
            if destination == original or original in destination.parents:
                raise ValueError('Cannot overwrite an original experiment')
    out.mkdir(parents=True, exist_ok=True)
    comparison_out.mkdir(parents=True, exist_ok=True)
    vintages = Vintages()
    old_panel = add_presence(vintages, enrich(vintages, vintages.panel()))
    panel = add_threshold_presence(vintages, old_panel)
    panels = {h: threshold_panel(panel, h) for h in HORIZONS}
    validation = []
    for start, end in FOLDS:
        origin = local_midnight(start)
        last = (pd.Timestamp(end)-pd.Timedelta(days=6)).strftime('%Y-%m-%d')
        for horizon, data in panels.items():
            train = data[(data.date < start) & (pd.to_datetime(data.label_available_at, utc=True) < origin)]
            val = data[data.date.between(start, last)].copy()
            check_fit_availability(val, local_midnight('2026-09-16'))
            p = val[['date', 'region', 'horizon', 'period_end', 'event', 'count_total',
                     'label_available_at', 'feature_available_at', 'origin']].copy()
            p['prior'] = val[f'prior{horizon}']
            p['logistic'] = predict_probability(train, val, origin)
            p['fold'] = start
            validation.append(p)
    validation = coherent_probabilities(pd.concat(validation, ignore_index=True))
    validation = append_baselines(validation, panels)
    macro = write_evaluation(validation, out)
    selected = choose_probability(macro[macro.model.isin(['prior', 'logistic'])])
    decision = {'selected': selected, 'criterion': 'lowest rolling-validation macro Brier; equal horizon and region weights; prior/logistic only',
                'event': 'at least one local day with >=3 archive-recorded starts in the selected window',
                'threshold': 3, 'comparison': '>=', 'horizons': list(HORIZONS), 'fold_windows': FOLDS,
                'common_origins_per_region': 67, 'logistic_C': .1,
                'features': FEATURES, 'postprocessing': 'cumulative maximum for prior/logistic before selection and inference',
                'additional_baselines': 'training frequency and majority class per region and fit; ties choose one; unsmoothed; fixed constants also reported',
                'auc': 'regional ROC AUC only for variable evaluation outcomes; macro excludes undefined regions; not selection',
                'independent_final_test': False}
    # Persist selection before evaluating the already-exposed diagnostic period.
    (out/'selection.json').write_text(json.dumps(decision, indent=2)+'\n', encoding='utf-8')
    reliability(validation, selected).to_csv(out/'reliability.csv', index=False)
    diagnostic = []
    diagnostic_origin = local_midnight('2026-09-16')
    features = panel[panel.date.between('2026-09-16', '2026-10-13')]
    for horizon, data in panels.items():
        train = data[(data.date < '2026-09-16') & (pd.to_datetime(data.label_available_at, utc=True) < diagnostic_origin)]
        p = features[['date', 'region']].merge(data[['date', 'region', 'event', 'count_total']], on=['date', 'region'], how='left', validate='one_to_one')
        p['horizon'] = horizon
        p['period_end'] = (pd.to_datetime(p.date)+pd.Timedelta(days=horizon-1)).dt.strftime('%Y-%m-%d')
        p['prior'] = features[f'prior{horizon}'].to_numpy()
        p['logistic'] = predict_probability(train, features, diagnostic_origin)
        diagnostic.append(p)
    diagnostic = coherent_probabilities(pd.concat(diagnostic, ignore_index=True))
    diagnostic = append_baselines(diagnostic, panels)
    diag_macro = write_evaluation(diagnostic, out, True)
    reliability(diagnostic, selected).to_csv(out/'diagnostic_reliability.csv', index=False)
    future_features = add_threshold_presence(vintages, add_presence(vintages, enrich(vintages, vintages.feature_rows(DAY))))
    future = []
    for horizon, data in panels.items():
        origin = local_midnight(DAY)
        train = data[pd.to_datetime(data.label_available_at, utc=True) < origin]
        p = future_features[['date', 'region', 'feature_available_at', 'feature_vintage']].copy()
        p['horizon'] = horizon
        p['period_end'] = (pd.Timestamp(DAY)+pd.Timedelta(days=horizon-1)).strftime('%Y-%m-%d')
        p['prior'] = future_features[f'prior{horizon}']
        p['logistic'] = predict_probability(train, future_features, origin)
        future.append(p)
    future = coherent_probabilities(pd.concat(future, ignore_index=True))
    future['probability'] = future[selected]
    future['probability_model'] = selected
    future['status'] = '>=3 daily archive-record event; not official alert probability'
    missing = pd.DataFrame([{'date': DAY, 'region': region, 'horizon': horizon,
                             'period_end': (pd.Timestamp(DAY)+pd.Timedelta(days=horizon-1)).strftime('%Y-%m-%d'), 'status': reason}
                            for region, reason in EXCLUDED.items() for horizon in HORIZONS])
    pd.concat([future, missing], ignore_index=True).sort_values(['horizon', 'region']).to_csv(out/'forecasts.csv', index=False)
    # The original experiment's saved forecasts are read, never overwritten/refitted.
    old_panels = {h: period_panel(old_panel, h) for h in HORIZONS}
    for diagnostic_flag, filename in [(False, 'validation_predictions.csv'), (True, 'diagnostic_predictions.csv')]:
        old = append_baselines(pd.read_csv(ROOT/'results/probability'/filename), old_panels)
        old_macro = write_evaluation(old, comparison_out, diagnostic_flag)
        print('ORIGINAL EVENT references:', 'diagnostic' if diagnostic_flag else 'validation')
        print(old_macro.to_string(index=False))
    print('>=3 VALIDATION:'); print(macro.to_string(index=False))
    print('Selected >=3 model:', selected)
    print('>=3 EXPOSED DIAGNOSTIC:'); print(diag_macro.to_string(index=False))
    verification = {'new_target': '>=3 on at least one local day; not window-total >=3',
                    'existing_probability_files_changed': False, 'new_sources': False,
                    'unknown_diagnostic_windows': int(diagnostic.event.isna().sum()),
                    'threshold_fixed_before_fit': True, 'selection_uses_validation_only': True}
    (out/'verification.json').write_text(json.dumps(verification, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/probability_ge3')
    parser.add_argument('--comparison-output', type=Path, default=ROOT/'results/probability_checks')
    args = parser.parse_args()
    run(args.output, args.comparison_output)


if __name__ == '__main__':
    main()
