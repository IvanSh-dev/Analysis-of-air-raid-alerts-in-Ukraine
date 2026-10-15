# Second experiment: limited ML improvement

The user requested lower error, a visual website and a README review after the original test had already been inspected. We retained that first experiment and explicitly treated its date range as exposed during the second iteration. There is no fresh independent final test for the new model.

Eight candidates were specified before execution, all evaluated on the same three chronological folds. The selected blend combines an MAE-trained pooled histogram gradient boosting regressor with the original seven-day mean, each at 50% weight. Trees use 7 leaves, learning rate 0.05, 150 iterations, minimum 30 rows per leaf, L2=1, seed 42, and no randomized internal validation. The two tree sizes and two blend weights are the entire tree search; no repeated search was performed after diagnostics.

| Validation window | Baseline MAE | Selected blend MAE |
| --- | ---: | ---: |
| June 15–July 12 | 1.744898 | 1.692071 |
| July 15–August 11 | 1.459406 | 1.442801 |
| August 15–September 12 | 2.022489 | 1.946991 |
| All 85 target dates, equal regional weight | 1.745561 | 1.696931 |

The reduction is 2.786% relative to the baseline. Its proximity to the weighted-mean candidate (MAE 1.701334) suggests restraint: this does not demonstrate a large or statistically proven ML advantage. No globally minimum error, high accuracy or safety utility is claimed.

On the already-exposed September 16–October 13 period, MAE is 2.001508 versus 2.048580 for the baseline, but bias worsens from -0.381322 to -0.610467. The improvement is modest and not uniform across regions. Per-region tables expose the full distribution. The next proper confirmation would be a predeclared future period after freezing this version.

## Reproduction and selection boundary

The runner reproduces both experiments and generates the site. `results/improved/selection.json` is written before any diagnostic prediction. Only `rolling_validation` scores are accepted by the selection function. Training labels must be known before each fit; all validation labels must be known before the simulated selection deadline. New derived features reuse the exact eligible historical snapshot, and tests mutate future snapshots to verify past features do not change.

The README was rewritten to describe the new commands, all feature availability, three fold boundaries, the eight candidates, current results, changed test status, site usage and explicit coverage limits. Original experiment documentation was preserved in `BASELINE_V1.md` with repaired relative links. Code and README are English; user explanations and dashboard are Ukrainian.

Model limitations remain: archive event definitions differ from actual alerts, geographic coverage is incomplete, source publication time is assumed, the sample is short and nonstationary, count spikes are hard to anticipate, and MAE optimization can produce systematic underprediction. Improving the metric cannot repair missing source truth.
