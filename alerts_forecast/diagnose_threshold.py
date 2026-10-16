"""Stage A only: inspect a fixed >=3 daily-record event without fitting models.

This module reads fixed-maturity labels and existing predictions. It neither
changes model selection nor writes into any existing experiment directory.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from threadpoolctl import threadpool_info

from .pipeline import ROOT, Vintages, EXCLUDED, local_midnight, check_fit_availability
from .improve import FOLDS, score
from .regions import LABELS, REGISTRY

HORIZONS = (1, 3, 7)
MIN_DAILY_RECORDS = 3  # Inclusive, confirmed by the owner before this diagnosis.
DIAGNOSTIC = ('2026-09-16', '2026-10-13')


def window_labels(panel, horizon):
    parts = []
    for region, group in panel.groupby('region', sort=True):
        group = group.sort_values('date').reset_index(drop=True)
        dates = pd.to_datetime(group.date)
        if not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError('Daily target dates must be contiguous')
        if not np.isfinite(group.y).all() or not group.y.ge(0).all():
            raise ValueError('Missing/invalid daily targets are not zeros')
        availability = pd.to_datetime(group.label_available_at, utc=True)
        if not availability.is_monotonic_increasing:
            raise ValueError('End-of-window label availability is not the latest')
        counts = pd.concat([group.y.shift(-k) for k in range(horizon)], axis=1)
        complete = counts.notna().all(axis=1)
        result = group[['date', 'region', 'feature_available_at', 'origin']].copy()
        result['horizon'] = horizon
        result['period_end'] = (dates + pd.Timedelta(days=horizon-1)).dt.strftime('%Y-%m-%d')
        result['label_available_at'] = availability.shift(-(horizon-1))
        result['event_ge3'] = np.nan
        result['event_any'] = np.nan
        result.loc[complete, 'event_ge3'] = counts.loc[complete].ge(MIN_DAILY_RECORDS).any(axis=1).astype(int)
        result.loc[complete, 'event_any'] = counts.loc[complete].gt(0).any(axis=1).astype(int)
        result['known'] = complete
        if result.loc[~complete, ['event_ge3', 'event_any', 'label_available_at']].notna().any().any():
            raise ValueError('Incomplete windows must retain missing labels')
        parts.append(result)
    return pd.concat(parts, ignore_index=True)


def stages(panels):
    validation = {h: [] for h in HORIZONS}
    for start, end in FOLDS:
        fit_origin = local_midnight(start)
        last = (pd.Timestamp(end)-pd.Timedelta(days=6)).strftime('%Y-%m-%d')
        for horizon, frame in panels.items():
            train = frame[(frame.date < start) & (frame.label_available_at < fit_origin)].copy()
            check_fit_availability(train, fit_origin)
            val = frame[frame.date.between(start, last)].copy()
            if not val.known.all():
                raise ValueError('Validation windows must have complete fixed-maturity outcomes')
            check_fit_availability(val, local_midnight(DIAGNOSTIC[0]))
            yield f'train_before_{start}', horizon, train, fit_origin.isoformat()
            yield f'validation_{start}', horizon, val, fit_origin.isoformat()
            validation[horizon].append(val)
    for horizon, frame in panels.items():
        yield 'validation_all_folds', horizon, pd.concat(validation[horizon]), ''
        diagnostic = frame[frame.date.between(*DIAGNOSTIC)].copy()
        yield 'exposed_diagnostic', horizon, diagnostic, local_midnight(DIAGNOSTIC[0]).isoformat()


def summarize(stage, horizon, frame, fit_origin):
    rows = []
    for region, group in frame.groupby('region', sort=True):
        known = group[group.known]
        if known.empty:
            raise ValueError('Supported region has no evaluable windows')
        rows.append({
            'stage': stage, 'horizon': horizon, 'region': region,
            'region_name': LABELS[region], 'status': 'supported archive proxy',
            'fit_origin': fit_origin, 'first_origin': group.date.min(),
            'last_origin': group.date.max(), 'last_known_origin': known.date.max(),
            'last_known_window_end': known.period_end.max(),
            'windows': len(group), 'known_windows': len(known),
            'unknown_windows': int((~group.known).sum()),
            'event_count': int(known.event_ge3.sum()),
            'event_rate': float(known.event_ge3.mean()),
            'old_event_rate': float(known.event_any.mean()),
            'constant_outcome': bool(known.event_ge3.nunique() == 1),
        })
    supported = pd.DataFrame(rows)
    if len(supported) != 23 or supported.known_windows.nunique() != 1:
        raise ValueError('Unexpected regional coverage or differing sample sizes')
    macro = {
        'stage': stage, 'horizon': horizon, 'regions': len(supported),
        'known_windows_per_region': int(supported.known_windows.iloc[0]),
        'unknown_windows_total': int(supported.unknown_windows.sum()),
        'first_origin': supported.first_origin.min(),
        'last_known_origin': supported.last_known_origin.max(),
        'last_known_window_end': supported.last_known_window_end.max(),
        'event_rate_macro': float(supported.event_rate.mean()),
        'old_event_rate_macro': float(supported.old_event_rate.mean()),
        'min_regional_rate': float(supported.event_rate.min()),
        'max_regional_rate': float(supported.event_rate.max()),
        'regions_below_005': int(supported.event_rate.lt(.05).sum()),
        'regions_above_095': int(supported.event_rate.gt(.95).sum()),
        'regions_constant': int(supported.constant_outcome.sum()),
    }
    for region, reason in EXCLUDED.items():
        rows.append({'stage': stage, 'horizon': horizon, 'region': region,
                     'region_name': LABELS[region], 'status': reason,
                     'known_windows': 0, 'event_rate': np.nan, 'old_event_rate': np.nan})
    return rows, macro


def existing_claims(out, panels):
    old = pd.read_csv(ROOT/'results/probability/diagnostic_predictions.csv')
    labels = pd.concat([frame[frame.date.between(*DIAGNOSTIC)] for frame in panels.values()])
    joined = old.merge(labels[['date', 'region', 'horizon', 'event_any']], on=['date', 'region', 'horizon'], validate='one_to_one')
    if len(joined) != len(old) or not np.allclose(joined.event, joined.event_any, equal_nan=True):
        raise ValueError('Reconstructed maturity labels do not match the shipped experiment')
    rows = []
    for (horizon, region), group in old[old.event.notna()].groupby(['horizon', 'region']):
        for name, predictions in [('always_one', np.ones(len(group))),
                                  ('always_zero', np.zeros(len(group))),
                                  ('logistic', group.logistic), ('prior', group.prior)]:
            rows.append({'horizon': horizon, 'region': region, 'model': name,
                         'n': len(group), 'observed_rate': float(group.event.mean()),
                         'brier': float(np.mean((np.asarray(predictions)-group.event.to_numpy())**2))})
    regional = pd.DataFrame(rows)
    macro = regional.groupby(['horizon', 'model'])[['brier', 'observed_rate']].mean().reset_index()
    regional.to_csv(out/'old_event_constant_by_region.csv', index=False)
    macro.to_csv(out/'old_event_constant_macro.csv', index=False)
    for stage in ['validation', 'diagnostic']:
        pred = pd.read_csv(ROOT/f'results/improved/{stage}_predictions.csv')
        _, recomputed = score(pred)
        stored = pd.read_csv(ROOT/f'results/improved/{stage}_macro.csv')
        matched = stored.merge(recomputed, on='model', suffixes=('_stored', '_recomputed'), validate='one_to_one')
        for metric in ['mae', 'rmse', 'bias']:
            if not np.allclose(matched[metric+'_stored'], matched[metric+'_recomputed'], rtol=0, atol=1e-12):
                raise ValueError('Stored count metric does not match stored predictions')
        recomputed['stage'] = stage
        recomputed.to_csv(out/f'count_{stage}_metrics_recomputed.csv', index=False)
    return macro


def preserved_files(out):
    paths = list((ROOT/'alerts_forecast').glob('*.py')) + [ROOT/'requirements.txt']
    paths += [p for p in (ROOT/'results').rglob('*') if p.is_file() and out not in p.parents]
    paths += [ROOT/'data/vintage_counts.csv.gz', ROOT/'data/vintage_counts.sha256']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = preserved_files(out)
    # Fail loudly if this diagnostic accidentally tries to fit any existing model.
    with ExitStack() as stack:
        for cls in [LogisticRegression, PoissonRegressor, HistGradientBoostingRegressor]:
            stack.enter_context(patch.object(cls, 'fit', side_effect=AssertionError('Stage A forbids model fitting')))
        vintages = Vintages()
        panel = vintages.panel()
        panels = {h: window_labels(panel, h) for h in HORIZONS}
        regional, macros = [], []
        for stage, h, frame, fit_origin in stages(panels):
            rows, macro = summarize(stage, h, frame, fit_origin)
            regional.extend(rows)
            macros.append(macro)
        regional = pd.DataFrame(regional)
        macro = pd.DataFrame(macros)
        regional.to_csv(out/'event_frequency_by_region.csv', index=False)
        macro.to_csv(out/'event_frequency_macro.csv', index=False)
        pd.concat(panels.values(), ignore_index=True).to_csv(out/'fixed_maturity_window_labels.csv', index=False)
        old_metrics = existing_claims(out, panels)
    versions = {name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'threadpoolctl']}
    requirements = dict(re.findall(r'^([^=\s]+)==([^\s]+)$', (ROOT/'requirements.txt').read_text(encoding='utf-8'), re.M))
    readme = (ROOT/'README.md').read_text(encoding='utf-8')
    record = {
        'run_at_utc': datetime.now(timezone.utc).isoformat(),
        'command': 'python -m alerts_forecast.diagnose_threshold',
        'step': 'A only; no new models or model selection',
        'threshold': MIN_DAILY_RECORDS, 'comparison': '>=',
        'definition': 'At least one local day with >=3 archive records in the whole horizon',
        'threshold_confirmed_by_owner': True,
        'training_frequencies': 'Separate expanding training set for each rolling-validation fit; only labels available before that fit',
        'validation_origins': 'Same 67 common forecast origins per region and horizon as the existing probability experiment',
        'diagnostic_origin_range': DIAGNOSTIC,
        'unknown_tail_windows': 'Retained missing; excluded from event-rate denominator',
        'supported_territories': 23, 'registry_territories': len(REGISTRY),
        'excluded_territories': EXCLUDED,
        'model_fit_calls_blocked': True,
        'existing_count_metrics_recomputed_from_saved_predictions': True,
        'fresh_model_rerun_performed': False,
        'linux_mae_reported_by_owner': 1.695790,
        'linux_report_independently_reproduced': False,
        'linux_versions_or_row_predictions_provided': False,
        'cross_platform_cause': 'Unresolved; library/runtime equivalence and Linux outputs not established; no Linux runtime installed locally',
        'environment': {'python': sys.version, 'platform': platform.platform(), 'libraries': versions,
                        'installed_versions_match_relevant_pins': all(versions[k] == requirements[k] for k in versions),
                        'threadpools': threadpool_info()},
        'readme_has_roc_auc': bool(re.search(r'ROC\s*AUC|\bAUC\b', readme, re.I)),
        'readme_has_constant_probability_baseline': bool(re.search(r'always.?one|always.?zero|constant (?:baseline|probab)', readme, re.I)),
        'brier_interpretation': 'Saturation makes small absolute scores possible; Brier still distinguishes probabilities. A constant win is meaningful, not proof that Brier cannot discriminate.',
        'preserved_files_sha256': original,
    }
    if original != preserved_files(out):
        raise ValueError('Existing sources/data/results changed during diagnostics')
    (out/'verification.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print('STEP A: inclusive >=3; no model fitting; existing files unchanged.\n')
    print('OLD EVENT: recomputed exposed-diagnostic scores (equal regional weights)')
    print(old_metrics.to_string(index=False, float_format=lambda x: f'{x:.9f}'))
    print('\nNEW EVENT: expanding training sets and evaluation windows')
    print(macro[['stage', 'horizon', 'known_windows_per_region', 'unknown_windows_total',
                 'first_origin', 'last_known_origin', 'last_known_window_end', 'event_rate_macro',
                 'old_event_rate_macro', 'regions_below_005', 'regions_above_095', 'regions_constant']].to_string(index=False, float_format=lambda x: f'{x:.9f}'))
    print('\nCOUNT METRICS: recalculated from shipped predictions, not new fits')
    for name in ['validation', 'diagnostic']:
        table = pd.read_csv(out/f'count_{name}_metrics_recomputed.csv')
        print(table[table.model.isin(['baseline_7', 'blend_7'])].to_string(index=False, float_format=lambda x: f'{x:.9f}'))
    print('\nREGIONAL EVENT RATES: validation and exposed diagnostic')
    table = regional[regional.status.eq('supported archive proxy') & regional.stage.isin(['validation_all_folds', 'exposed_diagnostic'])]
    print(table.pivot(index='region', columns=['stage', 'horizon'], values='event_rate').to_string(float_format=lambda x: f'{x:.6f}'))
    print('\nENVIRONMENT:', json.dumps(record['environment'], ensure_ascii=True))
    print('LINUX CAUSE: unresolved; no retraining or Linux reproduction in step A.')
    print('README CHECK:', json.dumps({k: record[k] for k in ['readme_has_roc_auc', 'readme_has_constant_probability_baseline']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/probability_ge3_diagnostics')
    run(parser.parse_args().output)


if __name__ == '__main__':
    main()
