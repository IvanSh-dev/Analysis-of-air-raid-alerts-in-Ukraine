# Binary probabilities and selectable periods

The user explicitly selected **probability of at least one archive record**, not percentage change in a count. The event is `sum(fixed-maturity daily archive counts over the selected window) > 0`. Periods are 1, 3 or 7 local calendar days, beginning October 16, 2026. The seven-day window ends October 22 inclusive. These are not live forecasts or probabilities of official alerts, danger or safety.

## Method

Each horizon has a separately fitted pooled logistic regression (L2, C=0.1, max_iter=1000, seed=42). Inputs reuse the historical-vintage count features plus observed presence rates over the preceding 7/28 eligible dates. Scaling and regional encoding are fitted on training rows only; no class balancing distorts the probability prior. An all-one-class training sample uses a smoothed constant instead.

Baseline probability is the proportion of fully elapsed historical windows containing any record, using the same 28-day eligible history, with Beta(1,1) smoothing. This avoids exact zero/one probabilities from short histories.

The event definitions are nested, so a non-learned cumulative maximum enforces `P(any in 1 day) <= P(any in 3 days) <= P(any in 7 days)`. It is applied to both candidates **before** validation scoring and deployment. No independence between days is assumed. The percentage is not derived from a Poisson distribution or the point count forecast.

The already selected `blend_7` count configuration is refitted for each period's average daily count, then multiplied by period length. These are point forecasts optimized partly for absolute error; they should not be interpreted as guaranteed conditional means. Count metrics for every horizon and region are exported independently of probability metrics. No new count search is performed.

## Timing and evaluation

All features are fixed at the beginning of a forecast window. A seven-day forecast does not use observations from its second or later days. Target counts retain each day's fixed maturity snapshot. A training window is usable only when its **last** target day has a known label before fit time. Noncontiguous/incomplete target windows are rejected or excluded, never filled with zero.

We reuse three past folds, with common forecast origins for all horizons:

| Fit origin | Forecast origins evaluated | Last possible seven-day target date | Origins/region |
| --- | --- | --- | ---: |
| 2026-06-15 00:00 Kyiv | June 15–July 6 | July 12 | 22 |
| 2026-07-15 00:00 Kyiv | July 15–August 5 | August 11 | 22 |
| 2026-08-15 00:00 Kyiv | August 15–September 6 | September 12 | 23 |

That is 67 origins per region/horizon, 1,541 region-origin observations per horizon. Windows overlap for 3/7 days, so observations are not independent. No standard-error or statistical-significance claim is made. Model choice uses mean macro Brier across horizons with equal region/horizon weight. The original exposed final-test dates do not enter this selection; a fresh independent confirmation period is still unavailable.

| Days | Logistic Brier | Baseline Brier | Logistic log loss | Observed event rate |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.075362 | **0.074905** | 0.243597 | 79.10% |
| 3 | **0.057914** | 0.057955 | 0.173208 | 88.38% |
| 7 | **0.047803** | 0.051990 | 0.146575 | 93.71% |

Logistic regression wins averaged over all three horizons, but the one-day baseline is slightly better. The site explicitly displays the worsening at one day. Brier and log loss are proper probability scores; accuracy would conceal class imbalance here. Reliability bins compare average predicted probabilities with observed frequencies; those bins were inspected, not used to fit an extra calibration layer. No perfect calibration is claimed.

## UI consistency rules

The latest already-exposed period is also evaluated after selection, without changing any choice. Forecast origins start September 16; only windows ending by the latest mature October 13 target are scored: 28 one-day, 26 three-day and 22 seven-day origins per region. Later unfinished windows retain missing outcomes; their 184 unknown region-window labels are not treated as zero. These are descriptive diagnostics, not a new independent test.

| Days | Exposed-period logistic Brier | Exposed-period baseline Brier |
| --- | ---: | ---: |
| 1 | **0.043745** | 0.046268 |
| 3 | **0.028379** | 0.029572 |
| 7 | 0.015916 | **0.012562** |

The baseline is better at seven days on this exposed period; it does not replace the validation-selected model. The site's evaluation selector changes metrics, calibration and historical graphs together. Top summary cards remain explicitly labelled as validation results.

* Every map shape joins by an explicit ISO code to exactly one of the 27 registry territories.
* Four unsupported territories have null probabilities/counts for every horizon; map hatching and unavailable messages preserve that state.
* Period selection updates dates, percentages, map colors, regional details, count forecasts, validation metrics and graphs from the same generated payload.
* The validation graph uses the last fold's August 15–September 6 forecast origins; actual binary events are shown as 0/100%, not as an observed probability.
* Very large/small probabilities display `>99.9%` / `<0.1%` rather than rounding to certainty.
* CSV and Telegram use the same exported probabilities/counts. No bot username or running status is invented.

Results: `results/probability/`. Executable entry point: `python -m alerts_forecast.periods`. The archive/publication and incomplete-coverage limitations from SOURCES.md still apply.
