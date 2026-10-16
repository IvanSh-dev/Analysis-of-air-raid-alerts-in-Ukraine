# Fixed >=3 daily-record event: Stage A diagnosis

Date: 2026-10-16 (Europe/Kyiv). The owner confirmed the inclusive comparison: a day with exactly three records qualifies. The target is at least one such local day in the entire 1/3/7-day window, not a window total of three.

## Executed command and evidence

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.diagnose_threshold
```

Every numeric result below comes from that execution, preserved verbatim in [command_output.txt](../results/probability_ge3_diagnostics/command_output.txt). Full precision is retained in the CSV files. No model was fitted: fit methods for the existing Poisson, logistic and histogram-boosting estimators were patched to fail during the diagnosis.

## Verification of the original event

| horizon | Observed event rate | always_one | always_zero | logistic | prior |
| --- | --- | --- | --- | --- | --- |
| 1 | 90.993789% | 0.090062112 | 0.909937888 | 0.043744593 | 0.046268116 |
| 3 | 95.150502% | 0.048494983 | 0.951505017 | 0.028378732 | 0.029572024 |
| 7 | 98.814229% | 0.011857708 | 0.988142292 | 0.015915928 | 0.012562445 |

The reported event frequencies and constant-one Brier scores are confirmed. Constant one beats both existing probability forecasts at seven days. However, Brier does distinguish models: at one and three days the logistic forecast has lower error than constant one. Rare negative outcomes make small absolute Brier values easy to obtain; they do not invalidate the score or establish ranking quality. ROC AUC and trivial probability baselines are absent from the current README; adding them is reserved for step C.

## New-event frequencies and exact temporal boundaries

Training expands separately at each rolling-validation fit. The table reports eligible origins only; all training labels are available before the fold fit under the unchanged commit-plus-six-hours rule. Validation uses the existing common origins across horizons. Diagnostic tails remain missing, rather than being replaced with non-events. Rates are equal-weight means over the supported regions. The four unsupported territories are present in the regional CSV with missing frequencies and explicit reasons.

| stage | horizon | first_origin | last_known_origin | last_known_window_end | known_windows_per_region | event_rate_macro | regions_below_005 | regions_above_095 | regions_constant | unknown_windows_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_before_2026-06-15 | 1 | 2026-05-01 | 2026-06-12 | 2026-06-12 | 43 | 58.948433% | 1 | 4 | 4 | 0 |
| validation_2026-06-15 | 1 | 2026-06-15 | 2026-07-06 | 2026-07-06 | 22 | 56.126482% | 5 | 5 | 5 | 0 |
| train_before_2026-06-15 | 3 | 2026-05-01 | 2026-06-10 | 2026-06-12 | 41 | 74.337222% | 0 | 11 | 5 | 0 |
| validation_2026-06-15 | 3 | 2026-06-15 | 2026-07-06 | 2026-07-08 | 22 | 72.924901% | 1 | 13 | 11 | 0 |
| train_before_2026-06-15 | 7 | 2026-05-01 | 2026-06-06 | 2026-06-12 | 37 | 86.016451% | 0 | 15 | 14 | 0 |
| validation_2026-06-15 | 7 | 2026-06-15 | 2026-07-06 | 2026-07-12 | 22 | 83.003953% | 1 | 17 | 18 | 0 |
| train_before_2026-07-15 | 1 | 2026-05-01 | 2026-07-12 | 2026-07-12 | 73 | 57.653365% | 2 | 5 | 3 | 0 |
| validation_2026-07-15 | 1 | 2026-07-15 | 2026-08-05 | 2026-08-05 | 22 | 60.474308% | 6 | 8 | 13 | 0 |
| train_before_2026-07-15 | 3 | 2026-05-01 | 2026-07-10 | 2026-07-12 | 71 | 72.872015% | 0 | 11 | 4 | 0 |
| validation_2026-07-15 | 3 | 2026-07-15 | 2026-08-05 | 2026-08-07 | 22 | 68.774704% | 5 | 15 | 17 | 0 |
| train_before_2026-07-15 | 7 | 2026-05-01 | 2026-07-06 | 2026-07-12 | 67 | 82.933160% | 0 | 14 | 13 | 0 |
| validation_2026-07-15 | 7 | 2026-07-15 | 2026-08-05 | 2026-08-11 | 22 | 74.703557% | 4 | 16 | 19 | 0 |
| train_before_2026-08-15 | 1 | 2026-05-01 | 2026-08-12 | 2026-08-12 | 104 | 58.528428% | 3 | 7 | 3 | 0 |
| validation_2026-08-15 | 1 | 2026-08-15 | 2026-09-06 | 2026-09-06 | 23 | 67.296786% | 3 | 9 | 11 | 0 |
| train_before_2026-08-15 | 3 | 2026-05-01 | 2026-08-10 | 2026-08-12 | 102 | 72.037511% | 0 | 13 | 4 | 0 |
| validation_2026-08-15 | 3 | 2026-08-15 | 2026-09-06 | 2026-09-08 | 23 | 79.206049% | 2 | 16 | 15 | 0 |
| train_before_2026-08-15 | 7 | 2026-05-01 | 2026-08-06 | 2026-08-12 | 98 | 80.301686% | 0 | 14 | 13 | 0 |
| validation_2026-08-15 | 7 | 2026-08-15 | 2026-09-06 | 2026-09-12 | 23 | 86.200378% | 2 | 18 | 20 | 0 |
| validation_all_folds | 1 | 2026-06-15 | 2026-09-06 | 2026-09-06 | 67 | 61.388709% | 4 | 7 | 4 | 0 |
| exposed_diagnostic | 1 | 2026-09-16 | 2026-10-13 | 2026-10-13 | 28 | 77.639752% | 1 | 12 | 10 | 0 |
| validation_all_folds | 3 | 2026-06-15 | 2026-09-06 | 2026-09-08 | 67 | 73.718365% | 3 | 13 | 10 | 0 |
| exposed_diagnostic | 3 | 2026-09-16 | 2026-10-11 | 2026-10-13 | 26 | 86.789298% | 1 | 18 | 18 | 46 |
| validation_all_folds | 7 | 2026-06-15 | 2026-09-06 | 2026-09-12 | 67 | 81.375730% | 0 | 16 | 15 | 0 |
| exposed_diagnostic | 7 | 2026-09-16 | 2026-10-07 | 2026-10-13 | 22 | 90.513834% | 1 | 20 | 21 | 138 |

The target is less saturated in the macro average, including on rolling validation. It is still highly saturated in many individual regions, especially at seven days. For example, only two regions have variable seven-day diagnostic outcomes; regional ROC AUC would be undefined for the others. Do not substitute an arbitrary AUC of 0.5 for constant outcomes.

Keep the threshold and all requested horizons unchanged unless the owner authorizes a different task. Based on rolling validation, the one-day event is the more informative main presentation; longer windows should retain explicit saturation diagnostics. Keep the count forecast alongside the event probability. A new prospective evaluation, when data become available, would be needed to establish future performance. No target, model or horizon is selected using the exposed diagnostic period.

## Regional frequencies

The following tables are computed from the same execution. Unsupported regions are not inserted as zeros. Machine-readable training, validation and diagnostic rates, including each fold and all registry territories, are in [event_frequency_by_region.csv](../results/probability_ge3_diagnostics/event_frequency_by_region.csv).

### train_before_2026-06-15

| Region | 1 day | 3 days | 7 days |
| --- | --- | --- | --- |
| Івано-Франківська | 4.651% | 14.634% | 37.838% |
| Волинська | 74.419% | 95.122% | 100.000% |
| Вінницька | 13.953% | 29.268% | 54.054% |
| Дніпропетровська | 100.000% | 100.000% | 100.000% |
| Донецька | 88.372% | 100.000% | 100.000% |
| Житомирська | 46.512% | 73.171% | 89.189% |
| Запорізька | 100.000% | 100.000% | 100.000% |
| Київська | 72.093% | 92.683% | 100.000% |
| Кіровоградська | 65.116% | 97.561% | 100.000% |
| Львівська | 34.884% | 65.854% | 89.189% |
| Миколаївська | 90.698% | 97.561% | 100.000% |
| Одеська | 72.093% | 90.244% | 100.000% |
| Полтавська | 93.023% | 97.561% | 100.000% |
| Рівненська | 16.279% | 36.585% | 67.568% |
| Сумська | 100.000% | 100.000% | 100.000% |
| Тернопільська | 6.977% | 19.512% | 43.243% |
| Харківська | 100.000% | 100.000% | 100.000% |
| Херсонська | 88.372% | 97.561% | 100.000% |
| Хмельницька | 11.628% | 29.268% | 56.757% |
| Черкаська | 44.186% | 80.488% | 97.297% |
| Чернівецька | 6.977% | 19.512% | 43.243% |
| Чернігівська | 93.023% | 97.561% | 100.000% |
| м. Київ | 32.558% | 75.610% | 100.000% |

### train_before_2026-07-15

| Region | 1 day | 3 days | 7 days |
| --- | --- | --- | --- |
| Івано-Франківська | 4.110% | 12.676% | 31.343% |
| Волинська | 68.493% | 95.775% | 100.000% |
| Вінницька | 12.329% | 29.577% | 56.716% |
| Дніпропетровська | 100.000% | 100.000% | 100.000% |
| Донецька | 87.671% | 98.592% | 100.000% |
| Житомирська | 36.986% | 66.197% | 94.030% |
| Запорізька | 97.260% | 100.000% | 100.000% |
| Київська | 63.014% | 94.366% | 100.000% |
| Кіровоградська | 71.233% | 97.183% | 100.000% |
| Львівська | 35.616% | 69.014% | 91.045% |
| Миколаївська | 93.151% | 98.592% | 100.000% |
| Одеська | 76.712% | 94.366% | 100.000% |
| Полтавська | 93.151% | 98.592% | 100.000% |
| Рівненська | 10.959% | 25.352% | 47.761% |
| Сумська | 100.000% | 100.000% | 100.000% |
| Тернопільська | 5.479% | 15.493% | 34.328% |
| Харківська | 100.000% | 100.000% | 100.000% |
| Херсонська | 90.411% | 98.592% | 100.000% |
| Хмельницька | 8.219% | 21.127% | 41.791% |
| Черкаська | 41.096% | 77.465% | 91.045% |
| Чернівецька | 4.110% | 11.268% | 23.881% |
| Чернігівська | 95.890% | 98.592% | 100.000% |
| м. Київ | 30.137% | 73.239% | 95.522% |

### train_before_2026-08-15

| Region | 1 day | 3 days | 7 days |
| --- | --- | --- | --- |
| Івано-Франківська | 2.885% | 8.824% | 21.429% |
| Волинська | 72.115% | 97.059% | 100.000% |
| Вінницька | 10.577% | 26.471% | 51.020% |
| Дніпропетровська | 100.000% | 100.000% | 100.000% |
| Донецька | 84.615% | 99.020% | 100.000% |
| Житомирська | 30.769% | 57.843% | 84.694% |
| Запорізька | 95.192% | 100.000% | 100.000% |
| Київська | 69.231% | 95.098% | 100.000% |
| Кіровоградська | 75.000% | 98.039% | 100.000% |
| Львівська | 46.154% | 77.451% | 93.878% |
| Миколаївська | 95.192% | 99.020% | 100.000% |
| Одеська | 83.654% | 96.078% | 100.000% |
| Полтавська | 95.192% | 99.020% | 100.000% |
| Рівненська | 8.654% | 20.588% | 37.755% |
| Сумська | 100.000% | 100.000% | 100.000% |
| Тернопільська | 3.846% | 10.784% | 23.469% |
| Харківська | 100.000% | 100.000% | 100.000% |
| Херсонська | 93.269% | 99.020% | 100.000% |
| Хмельницька | 5.769% | 14.706% | 28.571% |
| Черкаська | 36.538% | 71.569% | 92.857% |
| Чернівецька | 2.885% | 7.843% | 16.327% |
| Чернігівська | 97.115% | 99.020% | 100.000% |
| м. Київ | 37.500% | 79.412% | 96.939% |

### validation_all_folds

| Region | 1 day | 3 days | 7 days |
| --- | --- | --- | --- |
| Івано-Франківська | 1.493% | 4.478% | 10.448% |
| Волинська | 71.642% | 97.015% | 100.000% |
| Вінницька | 17.910% | 40.299% | 77.612% |
| Дніпропетровська | 100.000% | 100.000% | 100.000% |
| Донецька | 83.582% | 98.507% | 100.000% |
| Житомирська | 26.866% | 58.209% | 85.075% |
| Запорізька | 92.537% | 100.000% | 100.000% |
| Київська | 70.149% | 97.015% | 100.000% |
| Кіровоградська | 88.060% | 100.000% | 100.000% |
| Львівська | 62.687% | 88.060% | 100.000% |
| Миколаївська | 98.507% | 100.000% | 100.000% |
| Одеська | 92.537% | 100.000% | 100.000% |
| Полтавська | 97.015% | 100.000% | 100.000% |
| Рівненська | 4.478% | 13.433% | 40.299% |
| Сумська | 100.000% | 100.000% | 100.000% |
| Тернопільська | 1.493% | 4.478% | 10.448% |
| Харківська | 100.000% | 100.000% | 100.000% |
| Херсонська | 97.015% | 100.000% | 100.000% |
| Хмельницька | 7.463% | 19.403% | 38.806% |
| Черкаська | 44.776% | 79.104% | 98.507% |
| Чернівецька | 1.493% | 4.478% | 10.448% |
| Чернігівська | 100.000% | 100.000% | 100.000% |
| м. Київ | 52.239% | 91.045% | 100.000% |

### exposed_diagnostic

| Region | 1 day | 3 days | 7 days |
| --- | --- | --- | --- |
| Івано-Франківська | 0.000% | 0.000% | 0.000% |
| Волинська | 75.000% | 100.000% | 100.000% |
| Вінницька | 75.000% | 96.154% | 100.000% |
| Дніпропетровська | 100.000% | 100.000% | 100.000% |
| Донецька | 75.000% | 100.000% | 100.000% |
| Житомирська | 96.429% | 100.000% | 100.000% |
| Запорізька | 100.000% | 100.000% | 100.000% |
| Київська | 100.000% | 100.000% | 100.000% |
| Кіровоградська | 100.000% | 100.000% | 100.000% |
| Львівська | 78.571% | 100.000% | 100.000% |
| Миколаївська | 100.000% | 100.000% | 100.000% |
| Одеська | 100.000% | 100.000% | 100.000% |
| Полтавська | 100.000% | 100.000% | 100.000% |
| Рівненська | 53.571% | 88.462% | 100.000% |
| Сумська | 100.000% | 100.000% | 100.000% |
| Тернопільська | 14.286% | 15.385% | 18.182% |
| Харківська | 100.000% | 100.000% | 100.000% |
| Херсонська | 85.714% | 100.000% | 100.000% |
| Хмельницька | 28.571% | 57.692% | 100.000% |
| Черкаська | 96.429% | 100.000% | 100.000% |
| Чернівецька | 21.429% | 38.462% | 63.636% |
| Чернігівська | 89.286% | 100.000% | 100.000% |
| м. Київ | 96.429% | 100.000% | 100.000% |

## Count-MAE reproduction claim

Recomputing metrics from the shipped predictions reproduces validation MAE 1.696931107 for blend_7 and 1.745560833 for baseline_7; diagnostic blend_7 MAE is 2.001507512. This verifies stored arithmetic, not a fresh model fit. The owner reports Linux validation MAE 1.695790; no Linux output, commit or library/runtime versions were supplied for independent comparison. The current Windows runtime matches the relevant dependency pins, and no local WSL distribution/runtime is installed. Therefore the discrepancy cannot yet be attributed specifically to the operating system, versions, numerical runtime, or differing inputs. A controlled rerun is deferred rather than falsely claimed during no-model stage A.

Exact current environment and preserved-file hashes are in [verification.json](../results/probability_ge3_diagnostics/verification.json). Existing modelling sources, data and result files were hash-checked before and after the diagnosis and stayed unchanged.

## Stop point

Only stage A and arithmetic/source checks of the three reported concerns are complete. Steps B–F, including new models/features, AUC additions, the expanded unit tests, full retraining and README conclusions, have not been performed.
