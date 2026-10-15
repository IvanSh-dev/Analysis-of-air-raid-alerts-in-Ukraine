# Experiment log

Chronological record. Earlier proposals and unfinished statuses below describe their stage, not the final implementation. The final scope is nationwide archive-proxy forecasting for 23 territories; Kyiv-only scope and the splice are not used for training.

## 2026-10-15 — source feasibility, no forecasting experiment yet

- Asked for the missing original assignment, geography, and API-token availability.
- Received the KSE letter; user selected all regions and requested API access.
- Verified Python launcher failure; bundled Python 3.12.14 works.
- Initial direct downloads failed due to network restrictions. Requested network access and successfully downloaded two pinned source CSVs after permission was granted.
- Executed inspect_sources.py. Found stale official-named data, exact duplicate records, mixed geographic levels, and uneven volunteer coverage.
- Inspected upstream processors: CSVs store completed alerts and can contain synthetic finishes. This affects historical data availability even for alert-start counts.
- Verified API documentation and token-application instructions. No token was requested on the user's behalf, no secret was read, and no authenticated API response was obtained.
- No forecasting pipeline, model, metrics, GitHub repository, or conversation export has been completed.

## 2026-10-15 — requested source splice

- User chose to proceed without an API token because of the deadline and requested official history through September 7, followed by volunteer history.
- Implemented the cutoff at 2026-09-08 00:00 Europe/Kyiv, using start time to assign records.
- Preserved source geography and line-number provenance, removed only exact original-row duplicates, and did not fill missing days with zero.
- Generated 191148 rows: 185430 official and 5718 volunteer. Removed 113845 exact official duplicates.
- Flagged September 7, the first archive day, and the snapshot day as incomplete. Other coverage remains unverified.
- Included compressed pinned inputs, their license, checksums, English documentation, and a runnable Python merge script.
- Four temporal boundary tests passed. Models and final time splits remain pending because source comparability and historical publication availability still need resolution.

## 2026-10-15 — suitability review before modelling

- User requested an audit and an explicit stop before training.
- Rechecked GitHub: main still points to the pinned October 15 commit.
- Retrieved Kyiv Digital city history and state successfully without a token; history HTTP date 2026-10-15 15:16:13 UTC. This source includes later October 15 events.
- Audited source parsers and observed mixed territorial levels. Found one Kyivska oblast interval containing seven district starts on 2025-10-28.
- Compared original archives over their shared period; the spliced output itself intentionally has no overlap.
- Fixed two pandas naming collisions in the audit implementation. A timestamp spot-check also exposed a microsecond/nanosecond assumption error in event matching; corrected with explicit nanosecond normalization, reran, and independently checked every exported pair using timestamp subtraction. Discarded preliminary results.
- Corrected 60-day Kyiv comparison: official 154 starts, volunteer 184, 63 one-to-one pairs within 120 seconds; equal daily counts on 23 of 60 days. Splice compatibility was not established.
- Proposed a narrower single-source Kyiv City target. Digital has 2712 starts, matching its counter, no repeated-state anomalies from 2024 onward, and a full returned state sequence through October 14. Publisher completeness and past publication/revision times remain limitations.
- Proposed training 2024-01-01 through 2026-07-31, validation 2026-08-01 through 2026-09-16, final test 2026-09-17 through 2026-10-14. Tested ordered/disjoint boundaries. Inspected recent data only for source QA; no model training, selection or accuracy evaluation performed.
- Stopping for the requested user review. Original merged CSV unchanged.

## 2026-10-15 — nationwide scope and versioned data

- The user rejected the Kyiv-only proposal and requested a nationwide model. We retained 22 oblasts plus Kyiv City, explicitly excluding stale Luhansk/Zakarpattia and absent Crimea/Sevastopol. No claim of complete Ukrainian coverage is made.
- The available archives could not establish a consistent actual-alert target across territorial levels. Changed to a single-source, explicitly labelled count of region-assigned volunteer archive records. This is a measurable proxy, not repaired ground truth.
- Downloaded and hashed 184 immutable daily CSV versions (April 15–October 15). Created 485,300 compact regional daily queries. Retained upstream MIT attribution.
- Used historical snapshots for features and fixed maturity snapshots for labels; added an explicit six-hour commit-time availability assumption. Actual first-publication times remain unverified.
- Fixed common dates before model evaluation: train May 1–July 29, validation August 1–September 12, test September 16–October 13. Gaps permit label maturity. Previous city-only date proposals were superseded.
- Initial Python launcher and temporary-directory failures were resolved by using an available Python 3.12.14 runtime and project-local temporary storage. Network/DNS failures interrupted dependency installation; retried after network permission was granted. These were environment failures, not model experiments.

## 2026-10-15 — executed baseline and one pooled model

- Implemented a seven-day historical mean and one pooled Poisson regression (alpha=0.1, no hyperparameter search). Fit standardization and regional encoding only on training rows.
- First full execution: validation macro MAE 1.868843 for baseline versus 2.509949 for Poisson (rounded here; CSV is authoritative). Selected baseline on validation and persisted the decision before test prediction/evaluation.
- Final test: baseline macro MAE 2.048580, Poisson 2.549936. The weaker model was reported, not retuned or hidden. The regional table exposes large Poisson overprediction in Dnipropetrovska.
- Computed MAE, RMSE and bias for every region and equal-weight regional macro averages. Saved every prediction, largest errors and three figures.
- Found 22 region-day counts revised after the target's fixed maturity snapshot. Historical features/labels were not replaced with revised latest values.
- Eight initial temporal/missingness/metric tests passed. Added three meaningful guard tests: test metrics rejected by model selection, fixed target vintages unaffected by future changes, and immature labels unavailable. This changed validation checks, not model settings or selection.
- The user attached the destination Git repository. Read its existing README/license and preserved its MIT license and existing ignore rules. An initial copy used the destination as the relative source directory and failed without changing project code; corrected the source to an absolute path and continued.
- The user's reflection emphasizes checking whether AI decisions match the original nationwide objective and verifying source compatibility and historical information availability. Reflection wording uses only executed changes and observed results.

See EXECUTION.md for the final clean-environment run and repeatability checks. The authentic conversation export is a separate submission artifact; this log is not a substitute for it.

## Final execution check

- Clean repository environment: 11 tests passed, full README runner exited successfully. A repeat run produced 13 byte-identical result files. No model choices changed after test inspection.

## Second iteration — requested ML improvement and dashboard

- User requested lower error, a website and README review. Acknowledged that the old final test had already been exposed; preserved it as diagnostic only for new development.
- Specified eight candidates, three forward validation windows, additional past-only summaries, and MAE-aligned pooled trees. One bounded comparison selected the 50/50 blend with 7-leaf boosting. Validation MAE decreased from 1.745561 to 1.696931; selected blend beat mean7 in all three windows. No tuning used diagnostic scores.
- Diagnostic MAE decreased from 2.048580 to 2.001508 but bias became more negative. Reported the tradeoff and lack of new independent confirmation.
- Created a Ukrainian responsive dashboard, exported actual outputs, and preserved all 27 territorial statuses. Browser checks covered search, unavailable states, sorting, selected-region chart, comparison tabs and CSV download; the download hash matched the source. No browser console errors were observed. Narrow layout had no horizontal overflow.
- Full updated README runner passed 15 tests and completed both experiments plus dashboard export. Repeated improved results were byte-identical. No model choices changed during repeatability checks.
- Read and rewrote README; archived original description and corrected relative links. Refreshed reflection and submission instructions to distinguish the two experiments.
- Site registration succeeded once. Initial local server was isolated by sandbox; approved host execution exposed it correctly. Sites packaging first lacked Git Bash in PATH, then MSYS could not initialize within the sandbox, then tar treated a Windows drive as a remote host. Resolved with approved execution, Git Bash PATH and --force-local. Renewed the expired short-lived credential for the same Site; no credential persisted. Native deployment reported success, owner-private. Production URL displays its expected ChatGPT sign-in gate; UI was tested locally.

## Third iteration — explicit probabilities, periods, map and bot

- User requested percentages, selectable forecast periods, a map, a site-content check and a Telegram bot. Clarified percentages: user chose probability of at least one archive record; user has no BotFather token and requested code/instructions.
- Added direct binary events for entire 1/3/7-day windows, point-in-time label availability through each window's last day, historical presence features, a smoothed-frequency baseline and regularized pooled logistic regression. Applied nested-event monotonic postprocessing before evaluation/inference; no conversion from point counts or assumption of independent days.
- Evaluated 67 common origins per region/horizon over three past folds. Average Brier selected logistic, while the one-day baseline remained slightly better; exported that result rather than claiming improvement at every horizon. No original exposed test scores selected these models.
- Built period controls and a real map from pinned geoBoundaries/OSM geometry for all 27 territories, with four unavailable states. Retained the separate ODbL notice; the map describes 2017 administrative boundaries, not combat lines.
- Implemented a reply-only Telegram bot using the same generated data, region/period buttons, private-command dispatch, token-safe errors, hidden-input setup and no-token dry-run. No bot was registered, no live API call was made and no Telegram message was sent.
- Thirty-two Python tests passed. Minimal-DOM JavaScript checks covered all 81 region/horizon states, map identity, missing values, count mode, search, calibration and exposed-period switching. An independent audit recomputed all 4,623 validation windows and 1,748 known diagnostic windows, preserving 184 unknown outcomes, and compared every public forecast field against CSV. These logic/data checks are explicitly not browser/layout QA.
- The browser rejected local file-URL navigation. No security workaround or fake screenshot was used. New UI layout remains unverified in a real browser.
- Exact requests for write access to the attached checkout did not grant it, so implementation remained in the permitted delivery copy. The official Sites source helper launched, but its stdin continuation was automatically rejected by the environment's granular approval policy. The new hosted publication therefore remains pending; no false deployment claim or credential-file workaround was made.
- README, bot setup, probability method, status report and actual verification evidence were updated. Earlier model experiments remain archived. The full isolated README run and output-identity result are recorded in V3_VERIFICATION.json.

## Original checkout synchronization and current hosted verification — October 16

The prepared version was copied into the original user repository with an external backup and intact Git history. `tools/run.ps1` completed from that directory with exit code 0 and 32 tests. Node checked all 81 states; the bot's no-token Kyiv/three-day dry-run succeeded. Thirteen probability outputs and six public website files matched the verified delivery bytes. The `/site` ignore rule was corrected so the UI can be committed. See ORIGINAL_CHECKOUT_VERIFICATION.json.

The private Site was then updated successfully through the official source/package/deploy flow. Authenticated desktop interaction and visual map checks passed, with no console errors, after explicit owner sign-in approval. See DASHBOARD.md and SITE_V3_DEPLOYMENT.json. The original unavailable-access status has been superseded; live Telegram delivery, mobile UI QA and GitHub push remain unperformed.

## Final review: public Vercel and registered bot — October 16, 2026

The owner supplied a Vercel URL and a registered Telegram username. The public Vercel page/assets, browser controls, missingness and CSV download were verified; the bot's public profile exists. Live bot replies were not verified by the review process. The archive main commit still matched the pinned October 15 source.

Rewrote the English README and current status/bot/hosting docs; replaced the bot's old private map link; replaced the obsolete unregistered-bot website text with the real link; corrected the diagnostic chart's accessibility label. Added regression checks for these actual issues. No model search or test-based selection was performed. The full README runner completed with 33 tests, and JavaScript checked 81 region/period states. Local review changes await Git push/Vercel deployment and bot restart; historical deployment evidence was preserved.

## Owner-assisted live Telegram check — October 16, 2026

The owner pasted live responses to `/forecast Київ 3` and `/forecast Закарпатська 1`. Both complete replies matched local renderer output after whitespace normalization, including probabilities/counts/dates, the unavailable-state explanation and the public Vercel link. Recorded the supplied text in TELEGRAM_MANUAL_CHECK.json. Updated current status to distinguish this owner-assisted check from direct assistant Telegram observation, which did not occur. No token was provided, no extra bot messages were sent by the assistant, and no code/model changes were needed. Callback buttons and continuous uptime remain outside this two-command check.

## No-console bot hosting — webhook prepared, not cloud-deployed

The owner reported that closing the polling console stops the bot and asked for a free alternative. Prepared a separate Vercel webhook project with the same canonical renderer and compact forecast data. Removed the bot runtime's unnecessary ML imports. Added secret-header authentication, bounded requests, short outbound timeouts, hidden-input registration with bot-identity and deployed-secret checks, and rollback to polling. No token was provided, no cloud project was created, no real Telegram API call was made, and no webhook was registered by the assistant.

The full README runner completed with 47 tests and unchanged model results; a final registration-probe regression brought the separately executed suite to 48 passing tests. All 81 UI states passed. The deployment imported with site-packages disabled and rendered all 81 region/horizon responses identically. Deployment instructions and free-plan limitations are in VERCEL_BOT.md; WEBHOOK_VERIFICATION.json records the boundary between offline checks and unperformed live deployment.
