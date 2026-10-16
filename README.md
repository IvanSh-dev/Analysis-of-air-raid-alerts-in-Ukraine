# Alert Atlas — regional alert archive forecasting

A reproducible Python project for KSE AI Agentic School Stage 2. It forecasts the number of archive-recorded alert starts and the probability of at least one such record for each supported Ukrainian region over **1, 3, or 7 calendar days**.

**[Public dashboard](https://analysis-of-air-raid-alerts-in-ukra.vercel.app/)** · **[Telegram bot: @air_alert_atlas_bot](https://t.me/air_alert_atlas_bot)** · [Source repository](https://github.com/IvanSh-dev/Analysis-of-air-raid-alerts-in-Ukraine)

**Research only:** these are forecasts of records in an incomplete volunteer archive, not probabilities of official alerts, danger, or safety. Follow official air-raid notifications.

![Local redesigned dashboard: guided regional forecast](docs/readable-home.jpg)

## What the demo shows

- A guided regional forecast: choose a territory and period, read one large percentage and its plain-language explanation, then explore the map. Historical graphs, model comparisons and technical metrics expand on demand. Body text is 18 px on desktop and 17 px on mobile.
- One common forecast origin: **2026-10-16 00:00 Europe/Kyiv**. The 1/3/7-day windows end on October 16/18/22, respectively.
- Coverage: **22 oblasts and Kyiv City**, or 23 supported territories in a 27-territory registry. Luhansk and Zakarpattia have stale histories; Crimea and Sevastopol are absent from the source. Their forecasts remain unavailable, never zero.
- Baseline/model comparisons, regional metrics, reliability bins, historical graphs, and CSV download.
- A registered Telegram bot using the same generated data, now hosted through a separate Vercel webhook. The owner confirmed it works after the no-console setup. Local polling remains an alternative; do not run it while the webhook is registered.

This is a **frozen research demonstration**, not an automatically updated service. A 7-day percentage means at least one archive record during the whole week, not an average daily probability. A new forecast origin requires fresh eligible snapshots and a new evaluation/prediction run.

The public Vercel page and bot profile were checked on October 16, 2026. The owner also supplied two live bot replies (Kyiv and unavailable Zakarpattia); both match the local renderer, including the public map link. This was an owner-assisted manual check, not a direct Telegram session operated by the assistant. See [final review](docs/FINAL_REVIEW.md) for the exact checks and remaining deployment steps.

## Reproduce

Tested on Windows with **Python 3.12.14**. Dependencies are pinned in `requirements.txt`. Installation needs internet; modelling then runs offline using the included versioned data and map geometry. No alert API token or paid service is required.

From the repository root in PowerShell:

```powershell
./tools/run.ps1 -Python python
```

If the system Python alias is unavailable, pass the full path to a working Python executable. The runner creates `.venv`, installs dependencies, runs tests, reproduces the original and improved count experiments, evaluates probabilities, and exports the dashboard. Each exit code is checked.

Equivalent commands:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m alerts_forecast.pipeline
./.venv/Scripts/python.exe -m alerts_forecast.improve
./.venv/Scripts/python.exe -m alerts_forecast.periods
./.venv/Scripts/python.exe tools/build_dashboard.py
```

On Linux/macOS use `python3` and `.venv/bin/python` for the explicit commands; those platforms have not been tested. Run from the repository root; a package installation is unnecessary.

For local viewing:

```powershell
./.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8765`; stop with Ctrl+C. `site/index.html` also opens directly. The website needs no Node packages, CDN, map tiles, or backend. Vercel serves `site/`; it does not train models or run Telegram polling. Publish static-file changes through the existing Vercel deployment workflow.

Optional JavaScript checks require Node.js:

```powershell
node --check site/app.js
node tests/check_dashboard.mjs
```

The latter checks all 81 region/period combinations with a minimal DOM fixture. It is a logic test, not a replacement for browser inspection.

## Data and counting rule

Source: [Vadimkin's Ukrainian air-raid sirens dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset), using `volunteer_data_en.csv` at immutable commit `22d0443d1d1cdf6a0a413c6d15c3078b5ed26127` from **2026-10-15**. Latest raw start: **2026-10-15 03:28:42 UTC**. Latest mature target: **2026-10-13**. The final source recheck still matched that commit; see [freshness evidence](docs/FINAL_PUBLIC_CHECK.json).

The compact input contains **184 immutable snapshots**, April 15–October 15, represented as **485,300 regional daily queries**. [Raw URLs and hashes](data/snapshot_manifest.json) · [Checksum](data/vintage_counts.sha256) · [Source MIT notice](data/SOURCE_LICENSE).

Daily target: distinct **`(region, started_at)`** keys whose start falls on local day `d`, counted in the first snapshot committed at or after local midnight `d+2` and before `d+3`. Period counts sum these fixed daily targets; the binary event is whether the sum exceeds zero. Later revisions do not replace targets retrospectively.

An investigated second source mixed oblast, district, and other territorial levels. It was not spliced into the modelling series: exact-row deduplication would not remove overlapping oblast/district representations of one alert. [Source audit and cleaning](docs/SOURCES.md) · [Coverage by territory](docs/COVERAGE.md).

Zero means an empty query in a fully read archive snapshot, **not proof of no real alerts**. Missing snapshots/windows are rejected or excluded, never zero-filled. The last complete day of actual alerts remains unverified for every territory.

Map: pinned **geoBoundaries gbOpen UKR ADM1**, 27 units, administrative boundaries represented in 2017, based on OpenStreetMap/Wambacher. It does not show combat lines or current control. [Geometry metadata/hash](data/geometry_source.json) · [Separate ODbL 1.0 notice](data/GEOMETRY_LICENSE.md).

## Preventing future-data leakage

A snapshot is eligible only when **Git commit time + 6 hours precedes the forecast origin**. This is an explicit assumption: actual first-publication times cannot independently be verified.

Features use an eligible historical snapshot: lags 2/3/7; means 7/28; medians 7/14; a weighted mean; trend; standard deviation; and presence rates 7/28. Historical windows start at `d-2`, because yesterday was unfinished at the previous daily update. Region identity and forecast-start weekday are known in advance.

Training labels must already be available before fitting. A multi-day training target requires the **last day of its entire window** to be known. Scaling and encoding are fitted only on training data. A 7-day forecast uses no later observations inside that window. Tests check timing boundaries, missingness, and immunity to future revisions.

## Models and evaluation

Count baseline: the previous 7 eligible days' mean. The initial pooled Poisson model lost to it. A bounded comparison of eight candidates over three forward folds selected a 50/50 blend of small histogram gradient boosting and the mean baseline. Validation macro MAE improved from **1.745561 to 1.696931 records per region-day** (about 2.8%). This is a count result, not probability accuracy. [Count experiment](docs/IMPROVEMENT.md).

Probabilities are evaluated separately. Each horizon has pooled logistic regression (`C=0.1`), compared with a smoothed historical-frequency baseline. A fixed cumulative maximum enforces `P(1 day) <= P(3 days) <= P(7 days)` for both candidates before scoring. No independence between days is assumed; percentages are not derived from point counts.

All regions use common chronological boundaries:

| Fit origin, Kyiv midnight | Probability forecast origins scored | Latest 7-day target |
| --- | --- | --- |
| 2026-06-15 | 2026-06-15–2026-07-06 | 2026-07-12 |
| 2026-07-15 | 2026-07-15–2026-08-05 | 2026-08-11 |
| 2026-08-15 | 2026-08-15–2026-09-06 | 2026-09-12 |

There are **67 origins per region per horizon**. Selection minimizes average macro Brier across horizons, with equal region/horizon weights. Lower Brier and log loss are better.

| Horizon | Logistic Brier | Baseline Brier | Logistic log loss |
| --- | ---: | ---: | ---: |
| 1 day | 0.075362 | **0.074905** | 0.243597 |
| 3 days | **0.057914** | 0.057955 | 0.173208 |
| 7 days | **0.047803** | 0.051990 | 0.146575 |

Logistic wins averaged across horizons; the one-day baseline is slightly better. Brier is mean squared probability error against a 0/1 outcome. Reliability bins compare predicted/observed frequencies, without proving perfect calibration. Overlapping 3/7-day windows are dependent; no statistical-significance claim is made.

**The original test, 2026-09-16–2026-10-13, was exposed before later iterations.** It is now an additional diagnostic, not a fresh independent test, and does not select the improved models. Only mature windows ending by October 13 are scored: 28/26/22 origins per region for 1/3/7 days. The 184 unfinished outcomes remain missing.

| Horizon | Diagnostic logistic Brier | Diagnostic baseline Brier |
| --- | ---: | ---: |
| 1 day | **0.043745** | 0.046268 |
| 3 days | **0.028379** | 0.029572 |
| 7 days | 0.015916 | **0.012562** |

The seven-day baseline is better there; the validation-selected family is unchanged. Regional scores/predictions are exported so aggregates cannot conceal regional performance. Independent confirmation requires a predeclared future period and fresh data. [Detailed probability method](docs/PROBABILITY_AND_PERIODS.md).

## Telegram bot

**Current hosting:** the owner deployed `deploy/telegram` as a separate Vercel project and confirmed the bot works after registration. The assistant verified HTTP 200 and webhook readiness at [the public endpoint](https://air-alert-atlas-bot-lilac.vercel.app/api/telegram). Readiness alone does not prove Telegram delivery; the working-bot report is owner-assisted evidence. See [the no-console hosting guide](docs/VERCEL_BOT.md) for reproduction and rollback. Vercel Hobby has personal-use eligibility and usage limits; free does not mean unlimited or guaranteed uptime.

Open **[@air_alert_atlas_bot](https://t.me/air_alert_atlas_bot)** and try `/start`, `/regions`, or:

```text
/forecast Київ 1
/forecast Київська 3
/forecast Харківська 7
```

It distinguishes Kyiv City from Kyiv oblast, includes period buttons, preserves unavailable forecasts, and links to the public Vercel map. It replies only to incoming private requests, without automatic alert warnings or broadcasts.

For local polling: `./tools/run_bot.ps1` reads the existing token through hidden input and passes `TELEGRAM_BOT_TOKEN` via the environment. Never put it in chat, source, command arguments, or Git. Keep one polling process running. Do not run polling while a webhook is registered. Static hosting alone does not keep polling alive. [Setup and actual verification](docs/TELEGRAM_BOT.md).

Offline check, without token/network:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.telegram_bot --dry-run "/forecast Київ 3"
```

## Repository contents

| Path | Purpose |
| --- | --- |
| `alerts_forecast/` | Preparation, timing checks, models, evaluation, bot |
| `data/` | Versioned compact input, provenance, hashes, geometry, licenses |
| `results/` | Original count results and three analysis figures |
| `results/improved/` | Count-model comparison and diagnostics |
| `results/probability/` | Predictions, regional/macro scores, reliability, selection |
| `site/` | Static dashboard, generated JSON/JS, 81 forecast rows: 69 numeric, 12 unavailable |
| `deploy/telegram/` | Generated, stdlib-only Vercel webhook project with compact identical forecasts |
| `tests/` | Temporal, missingness, selection, bot, UI checks |
| `tools/` | Reproduction, optional raw rebuild, export, bot launcher |
| `docs/` | Source audit, methods, coverage, experiment history, verification |
| `reflection.txt` | Separate 100-word English reflection for the submission form |

To reproduce probability outputs separately:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.periods --output .tmp/probability-reproduction
```

Submission requires the GitHub repository, an authentic full conversation text export, and a personally reviewed reflection of about 100 words. The standalone English [reflection.txt](reflection.txt) is ready to attach as a separate plain-text file (100 words). Local `submission/` materials are deliberately ignored by Git. Refresh the genuine export after the final assistant reply. The experiment log supplements it; it does not replace the conversation.
