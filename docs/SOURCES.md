# Sources and the target we can actually measure

Checked on 15 October 2026. This is a nationwide research project with partial geographic coverage. The data do **not** support a verified count of actual oblast-wide air-raid starts for every oblast. We therefore predict a clearly labelled proxy: records assigned to a region by a single volunteer archive.

## Verified source versions

The public [upstream repository](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) was checked against commit `22d0443d1d1cdf6a0a413c6d15c3078b5ed26127`, committed at `2026-10-15T03:50:46Z`. The latest main commit still matched this version at the freshness recheck. Downloading public CSVs needs no token. Upstream distributes the repository under MIT; its notice is retained in [SOURCE_LICENSE](../data/SOURCE_LICENSE).

| Source at this commit | First observed start, UTC | Last observed start, UTC | Assessment |
| --- | --- | --- | --- |
| `official_data_en.csv` | 2022-03-15 16:10:34 | 2026-09-07 05:28:22 | September 7 truncated; September 6 only a calendar candidate, not proven nationally complete |
| `volunteer_data_en.csv` | 2022-02-25 16:36:22 | 2026-10-15 03:28:42 | October 15 partial; October 14 calendar-complete but not yet mature under our fixed target rule |
| Kyiv Digital history, inspected separately | 2022-02-25 05:19:07 | 2026-10-15 13:54:39 | Fresher city-only history; cannot meet nationwide scope |

Latest finishes in the two CSVs are respectively September 7 05:39:33 UTC and October 15 03:44:15 UTC. Kyiv Digital's last returned state is October 15 14:19:12 UTC. The city API was successfully queried without a token, but it is used only as audit evidence, not as model input or redistributed raw data. [API documentation](https://kyiv.digital/open-api/docs/air-alert.html), [history](https://kyiv.digital/open-api/air-alert/history).

The most recent mature target day is **October 13** in the October 15 archive version. This is a maturity definition, not a claim of perfect real-world completeness. The project uses the latest checked public nationwide archive, not the stale official-named file. It does not claim that no newer source exists anywhere. Recheck upstream before submission if another daily release has appeared; do not silently replace pinned data or reuse the holdout for further selection.

## Why the requested splice is not used for training

The earlier merge was performed as requested: official starts before September 8 00:00 Europe/Kyiv, volunteer starts afterwards. The merge is an engineering artifact, not evidence of statistical compatibility.

* The official file has 299,275 rows, including 113,845 exact duplicates. Its 185,430 distinct rows split into 65,314 oblast, 99,304 raion and 20,812 hromada records. The volunteer file has 116,689 rows and no exact duplicate rows at this snapshot.
* One Kyivska oblast interval on October 28, 2025, 14:46:14–15:39:55 UTC contains seven district starts at 15:07:29–15:07:35. Exact deduplication leaves all eight rows. Adding them does not measure eight starts of oblast-wide coverage. Evidence: [overlapping rows](evidence/overlapping_geographies_example.csv).
* In 2026 through September 6, Kyivska has 3,416 district rows and no oblast rows; Lvivska has 501 district rows and no oblast rows. Filtering only `level=oblast` would discard their recent observations. Geography is not stable enough for a mechanical regional splice.
* Neither CSV contains an explicit alert type or original message identifier. The [official parser](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset/blob/22d0443d1d1cdf6a0a413c6d15c3078b5ed26127/processors/official_channel_processor.py) recognizes words/symbols; the [volunteer parser](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset/blob/22d0443d1d1cdf6a0a413c6d15c3078b5ed26127/processors/volunteer_etryvoga_processor.py) recognizes broad alert/threat terms and assigns a region using names. It can overwrite an active start or synthesize a finish. Both write completed records. The volunteer archive contains 5,877 naive finishes.
* Original files overlap, although the splice deliberately removes the overlap. For the same Kyiv City territory on July 9–September 6, official/volunteer counts are 154/184; only 63 starts match one-to-one within 120 seconds (77 within five minutes); daily totals agree on 23/60 days. [Matched timestamps](evidence/official_volunteer_last_60_days_pairs.csv), [comparison summary](evidence/source_comparison.csv). This is enough to reject assumed equivalence; it is not a comprehensive cross-region reconciliation.
* September 7 official data are truncated; an empty regional query there cannot mean zero actual alerts. On September 8, the first volunteer day in the splice, Kyiv has 3 volunteer records versus 4 Digital starts. Source switches and count shifts cannot be interpreted as military activity changes.

## One counting rule, applied everywhere

For region r and local calendar date d, count distinct `(region, started_at)` keys whose UTC start converts to d in `Europe/Kyiv`, **in the first pinned archive snapshot committed on or after local midnight d+2, before d+3**. Use one region label from the volunteer file; never add official oblast/district/community records. Identical starts for different region labels remain separate regional observations; summing regions is not a unique national incident count. Two true starts sharing an identical timestamp cannot be disambiguated without message IDs.

A successfully read snapshot with no such keys has zero **archive records**. This says nothing about the true number of alerts. Missing snapshot/query data raise an error. Luhansk, Zakarpattia, Crimea and Sevastopol receive unavailable forecasts, not zeros. Records spanning midnight belong only to their start day. Finishes, duration and `naive` are not features. An unfinished event absent from this completed-record archive may be missing from the proxy; no end is manufactured by this project. The fixed maturity rule makes the evaluated proxy explicit rather than pretending to repair that limitation.

The compact data include 184 daily versions from April 15 through October 15, 2026. Each manifest entry records immutable Git SHA, commit timestamp, exact raw URL, SHA-256, row counts and region endpoints. Counts cover April onward for feature warm-up. Compact zeros for the two stale source labels are only archive queries and are excluded from every modelling and evaluation step. Unknown actual counts remain unknown.

## Availability and revisions

A snapshot becomes eligible at **Git commit time + 6 hours**, strictly before a forecast origin. Commit time is not independently verified first-publication time; the buffer is a documented assumption, not proof. Delayed/backdated pushes beyond six hours would invalidate that assumption. Raw data publication/revision latency is otherwise undocumented. This is a retrospective backtest under an explicit availability assumption, not a live prospective trial.

Features use the eligible historical snapshot, never today's revised history. Labels use a fixed maturity snapshot. Training rows must have their label snapshot available before the simulated fit. There are 22 region-day queries in the model panel whose later October 15 totals differ from their fixed maturity labels. That is why latest-file lags and retrospective labels would give a different experiment. The code asserts temporal availability, but cannot certify upstream publication behavior.

The inclusion rule and dates were fixed after source quality checks, before forecasting. Coverage checks used the current source and therefore the evaluated cohort is retrospectively selected for archive availability. We report performance only for these 23 labels; it cannot be generalized to missing regions or to all actual Ukrainian alerts.
