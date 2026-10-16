> Archived count-model iteration. See root README for probability/period/map/bot additions.

# Alert Atlas — Ukraine archive forecasts

A reproducible Python project and interactive dashboard for KSE AI Agentic School Stage 2. Predicts next-day **region-assigned records in a volunteer alert archive**, separately for 22 oblasts and Kyiv City.

**Partial coverage, not verified real-alert counts.** Luhansk and Zakarpattia have stale data; Crimea and Sevastopol are absent. These territories appear without forecasts, never as zero actual alerts. Predictions must never replace official notifications. [Coverage](../docs/COVERAGE.md) · [Source audit](../docs/SOURCES.md).

## Reproduce everything

Tested on Windows with Python 3.12.14. No API token required. Initial dependency installation needs internet; data, training, evaluation and dashboard generation then work offline.

From the repository root in PowerShell:

```powershell
./tools/run.ps1 -Python python
```

If the system Python alias is unavailable, use `-Python "C:/path/to/python.exe"`. The runner creates `.venv`, installs pinned dependencies, runs 15 tests, reproduces the original experiment, evaluates improved candidates and exports the dashboard data. Every command's exit status is checked; temporary files remain in ignored `.tmp/`.

Equivalent explicit commands:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m alerts_forecast.pipeline
./.venv/Scripts/python.exe -m alerts_forecast.improve
./.venv/Scripts/python.exe tools/build_dashboard.py
```

On Linux/macOS use `python3` and `.venv/bin/python`; those platforms were not executed. Run from the repository root; installing this directory as a package is unnecessary.

## Dashboard

Open `site/index.html` directly in a browser, or run:

```powershell
./.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory site
```

Visit `http://127.0.0.1:8765`; stop with Ctrl+C. [Hosted preview and verification](../docs/DASHBOARD.md).

The Ukrainian interface supports region search, sorting, forecast selection, actual-versus-predicted graphs, validation/diagnostic comparison and CSV download. All 27 territories remain visible, including four unavailable ones. It has no JavaScript package, CDN or backend dependency. `site/data.js` and `site/forecasts.csv` are generated from real results. This is a **frozen October 16, 2026 demonstration**, not an automatically updating service. The GitHub link points to the project repository; local changes need pushing separately.

## What is forecast, and when

Origin: 00:00 at the beginning of the target date, `Europe/Kyiv`. Horizon: one local calendar day (23/24/25 hours across daylight saving). Fractional predictions are expected counts; evaluation uses unrounded values.

Target: count distinct `(region, started_at)` keys whose UTC start falls on local date d, in the first snapshot committed at/after midnight d+2 and before d+3. This fixed maturity rule defines an observable archive outcome, not complete ground truth. Overnight records count on their start date only. No official district/oblast rows are mechanically combined with volunteer records.

The latest checked upstream commit is `22d0443d1d1cdf6a0a413c6d15c3078b5ed26127`, October 15, 2026. Latest raw start: October 15 03:28:42 UTC. Latest mature target: **October 13**; October 14 is not mature and October 15 is partial. Included: 184 daily versions from April 15–October 15, compacted into 485,300 regional daily queries. [Manifest and raw hashes](../data/snapshot_manifest.json) · [Compact checksum](../data/vintage_counts.sha256) · [MIT source notice](../data/SOURCE_LICENSE).

A snapshot is eligible at commit time + six hours, strictly before origin. **This is an availability assumption:** actual first-publication times are not independently verified. Missing queries raise errors. Zero means an empty query in a fully read archive, never proven absence of actual alerts. Stale territories are excluded from modelling. Historical inputs use the then-eligible version; labels use a fixed maturity version and must be available before fitting. Twenty-two panel counts change in later snapshots.

| Input | Why available at origin |
| --- | --- |
| Region indicator | Fixed archive label |
| Lags 2, 3, 7 | Past elapsed dates in the eligible historical snapshot |
| Mean7 / mean28 | d-2…d-8 / d-2…d-29 in that same snapshot |
| Median7 / median14 | d-2…d-8 / d-2…d-15 |
| Weighted mean | d-2…d-29, weights proportional to 0.75^k, k=0…27 |
| Trend and standard deviation | Mean7 minus mean28; standard deviation of d-2…d-8 |
| Weekday sine/cosine | Future calendar date is known in advance |

Yesterday is skipped because the previous daily update precedes its end. Future finishes, threat texts and latest revisions are not features. Learned transformations in the original Poisson model use training rows only. The new tree model needs no scaling and learns splits from training rows only.

## Improved ML and honest evaluation

The original experiment compared mean7 against pooled Poisson regression; mean7 won. Its outputs remain in `results/` and its [description is preserved](../docs/BASELINE_V1.md). After the user requested better ML, we specified eight candidates before running the new comparison:

* Mean7, median7, median14 and exponentially weighted mean.
* Pooled histogram gradient boosting with 7 or 15 leaves, either alone or blended 50/50 with mean7.

Boosting uses absolute-error loss, aligned with MAE: 150 iterations, learning rate 0.05, minimum leaf size 30, L2=1, random seed 42, no internal random validation or early stopping. One model serves all regions using region identity and recent history. No neural network or extra data source was added.

All candidates share expanding-window validation. Only labels already available at each fit are included:

| Training target dates | Validation target dates | Days/region |
| --- | --- | ---: |
| 2026-05-01–2026-06-12 | 2026-06-15–2026-07-12 | 28 |
| 2026-05-01–2026-07-12 | 2026-07-15–2026-08-11 | 28 |
| 2026-05-01–2026-08-12 | 2026-08-15–2026-09-12 | 29 |

Selection minimizes MAE across out-of-window predictions, with equal weight for each of 23 regions (85 dates per region). The third window contributes one extra day within each regional average. Selection is persisted before diagnostic predictions. The selected candidate is refitted on May 1–September 12 before the September 16 diagnostic origin; the October 16 demonstration uses all labels known before that origin.

| Candidate | Rolling validation MAE |
| --- | ---: |
| **50% boosting, 7 leaves + 50% mean7** | **1.697** |
| Weighted mean | 1.701 |
| 50% boosting, 15 leaves + 50% mean7 | 1.703 |
| Median14 | 1.712 |
| Original mean7 baseline | 1.746 |
| Median7 | 1.771 |
| Boosting, 7 leaves | 1.787 |
| Boosting, 15 leaves | 1.810 |

The selected blend reduces validation MAE by **2.8%** against mean7 and beats it in each fold. Its advantage over the weighted mean is small. Statistical significance and globally minimal error are not established. Pure boosting loses to simpler forecasts, so additional model complexity is not automatically useful.

| Already-exposed period: September 16–October 13 | Macro MAE | Macro RMSE | Macro bias |
| --- | ---: | ---: | ---: |
| Mean7 | 2.049 | 2.623 | -0.381 |
| Selected blend | 2.002 | 2.595 | -0.610 |

**This is not a new independent final test.** The period was inspected in the first iteration. It is excluded from current selection, but engineering happened after exposure. The 2.3% diagnostic improvement is descriptive; the blend also underpredicts more on average. Fresh future outcomes are required for independent confirmation. The original once-held-out result remains separately documented; changing old date labels cannot undo exposure.

MAE measures average absolute count error; RMSE emphasizes large misses; bias is prediction minus observation. Macro values average regional metrics equally (macro RMSE is not pooled RMSE). MAPE is omitted because zero-count dates make it unstable. Per-region results, fold results and every forecast are available in `results/improved/`.

## Files and checks

* `alerts_forecast/pipeline.py`: original experiment and original graphs.
* `alerts_forecast/improve.py`: enhanced features, rolling selection, diagnostics and next-day forecasts.
* `results/improved/`: candidate scores, per-region/fold metrics, predictions and `selection.json`.
* `results/coverage.csv`: exact territorial endpoints and unavailable statuses.
* `tools/build_dashboard.py`, `site/`: actual-data export and responsive dashboard.
* `tests/`: 15 temporal, missingness, weighting and model-selection checks.
* `docs/EXPERIMENT_LOG.md`, `docs/EXECUTION.md`, `docs/IMPROVEMENT.md`: actual iterations, execution evidence and limitations.

Repeat the new evaluation without overwriting shipped outputs:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.improve --output .tmp/improved-reproduction
```

Optional provenance rebuild (184 downloads, about 1.5 GB uncompressed; unnecessary for ordinary execution):

```powershell
./.venv/Scripts/python.exe tools/rebuild_vintages.py --cache .vintage_cache --workers 4
```

Every raw snapshot is checked against its pinned SHA-256. Future data updates are new experiments: retain this frozen reference and define a new future holdout before observing it. Recheck data freshness if submitting after another daily archive release.
