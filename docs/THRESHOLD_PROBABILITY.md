# Separate inclusive >=3 daily-record probability experiment

Implemented on October 16, 2026, after the owner reviewed stage A and explicitly
authorized model implementation plus website/bot integration. No new data source,
threshold search or existing model/hyperparameter change was introduced.

## Definition and timing

The event is at least one local calendar day with three or more archive records
inside the 1/3/7-day window. Exactly three qualifies; a total of three spread over
three one-record days does not. This remains an archive proxy, not an official
alert, danger or safety probability. Unsupported territories remain missing.

The new module reuses fixed-maturity counts, the commit-plus-six-hours availability
assumption, the same rolling folds and common forecast origins. It adds >=3 daily
frequency over the last 7/28 eligible historical days, starting at d-2, and a
Beta(1,1)-smoothed frequency of threshold-window events. Logistic regression keeps
C=0.1, the existing preprocessing, iteration limit and random state. Learned
transformations and regional frequency/majority baselines use only eligible
training rows. A window's label must be available before fitting. Feature and
label timing are checked independently.

Cumulative maximum across horizons is applied to logistic/prior probabilities
before validation scoring, selection and inference. Additional training-frequency
and majority-class references are reported as fitted, without coherence adjustment;
their different eligible training-window lengths can produce non-nested estimates.
They do not participate in model selection. Majority ties choose one. Fixed all-one
and all-zero references are also shown. Brier uses raw probabilities; log loss clips
to [1e-8, 1-1e-8]. ROC AUC is computed per region only for variable outcomes and is
diagnostic, not a selection criterion. Undefined AUC remains missing.

## Executed commands and results

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.threshold_probability
./.venv/Scripts/python.exe tools/build_dashboard.py
./.venv/Scripts/python.exe tools/build_bot_deployment.py
./.venv/Scripts/python.exe -m pytest -q
node --check site/app.js
node tests/check_dashboard.mjs
```

Actual model output: [threshold_probability.txt](evidence/dual_target/threshold_probability.txt).
The table below is generated from its exported validation metrics.

| horizon | model | brier | log_loss | roc_auc | auc_regions |
| --- | --- | --- | --- | --- | --- |
| 1 | logistic | 0.094253 | 0.304600 | 0.550930 | 19 |
| 1 | prior | 0.095775 | 0.308874 | 0.573365 | 19 |
| 3 | logistic | 0.062905 | 0.213620 | 0.531967 | 13 |
| 3 | prior | 0.062022 | 0.215885 | 0.565858 | 13 |
| 7 | logistic | 0.064478 | 0.198092 | 0.551351 | 8 |
| 7 | prior | 0.058248 | 0.203995 | 0.600628 | 8 |

Mean validation Brier across horizons is 0.072015 for smoothed frequency
and 0.073879 for logistic regression. Therefore the new target selects
**prior**, even though logistic performs better on the already-exposed diagnostic.
No new independent final test is claimed. Stage A's regional saturation limitations
remain; the threshold and registry were not changed in response to diagnostics.

## Preservation and delivery

All three original pipelines were rerun into ignored temporary directories.
The [comparison record](evidence/dual_target/reproduction_check.json) confirms that
all checked existing regional/macro MAE, RMSE, bias, Brier and log-loss columns match
to six decimals. The committed original CSV files and original model sources were
not overwritten. Logs: [base](evidence/dual_target/pipeline.txt),
[count improvement](evidence/dual_target/improve.txt),
[original probability](evidence/dual_target/periods.txt).

The website and bot offer two explicit event choices. Counts always refer to all
archive records, not the number of days reaching the threshold. Generated Vercel
data includes both targets; legacy callback buttons still select the original
event. A missing new-target payload fails explicitly rather than falling back.

These are local reviewed changes. After Git push, both existing Vercel projects
must deploy the new commit: site root for the dashboard, deploy/telegram for the
webhook. The endpoint and existing secret/token do not change; webhook registration
does not need repeating for a code/data-only redeployment. Live delivery of this
new target has not been claimed or operated by the assistant.
