# Executed verification

Executed on October 15, 2026 in the user-supplied Git repository on Windows.

* Python 3.12.14; pandas 3.0.6; scikit-learn 1.9.1; matplotlib 3.11.2.
* Created a fresh `.venv` inside the actual destination repository using `tools/run.ps1 -Python <working Python executable>`, exactly the README's supported full-path alternative. The available bundled Python runtime was used because the system Python alias was not functional.
* Installed every pinned dependency. An initial network/DNS failure was resolved after network access was granted; installation and execution then completed with exit code 0.
* All **11 tests passed**. Full preparation, both forecasts, validation selection, final test, forecast demonstration and figure generation completed.
* Repeated the documented pipeline command with `--output .tmp/reproduction`. All **13 output files** were byte-identical, including metrics, predictions, decision, coverage and plots. This was a reproducibility check, not additional model tuning.
* Independently checked unique region/day keys, available features, nonmissing model inputs, 27 registry entries, 23 numeric forecasts, and missing forecasts for all excluded territories. Unknown actual-alert completeness remains missing for every region.
* Visually inspected all three generated figures; region labels, legends and date axes are readable.
* Checked local README/source-document links. Retained the existing repository license and ignore rules.

Machine-readable hashes and environment: [execution_record.json](execution_record.json).

Not executed or established: prospective live forecasting, guaranteed first-publication times, true alert completeness, cross-platform runs, or GitHub publication. Repository changes remain local and ready to review/commit. No API token is needed for this version.

## Second iteration: improved ML and dashboard

The updated README runner completed successfully with 15 tests, both experiments and dashboard export. A repeat of the improved pipeline produced 9 byte-identical files. All README/local documentation links checked here resolve. See [improved_execution.json](improved_execution.json), [model comparison](IMPROVEMENT.md) and [browser/deployment checks](DASHBOARD.md). The original execution record above remains a historical record, not the latest test count.

## Third iteration verification

See [V3_VERIFICATION.json](V3_VERIFICATION.json) and [status/blocks](V3_STATUS.md). Thirty-two Python tests passed; minimal-DOM checks covered 81 regional/period states. Independently recomputed 4,623 validation and 1,748 diagnostic windows. New browser layout, hosted publication and real Telegram delivery are not claimed as tested.

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

## Real Vercel deployment failure: import-only entrypoint — October 16, 2026

The owner reported `[unused_function]` for `api/telegram.py` during deployment. The initial local import/handler tests had passed, but did not cover Vercel static discovery. Checked the official Vercel detector and ran its published `@vercel/python-analysis@0.15.0` package against both source variants: import-only returned null; an explicit local handler class returned `handler`. Updated the generator and regenerated the entrypoint, preserving the shared implementation. Added a regression checking the actual local class declaration, module identity and BaseHTTPRequestHandler inheritance. All 49 Python tests passed. This verifies discovery with the official analyzer, not a successful cloud deployment; a new commit/deployment is still required. No secret, model or forecast changed.

## Readability revision and owner-confirmed cloud bot — October 16, 2026

The owner confirmed the Vercel bot works after the no-console registration workflow. Endpoint readiness was independently verified in the preceding conversation turn; no assistant Telegram session or credential sharing occurred. This supersedes earlier pending-deployment status entries. The website was then simplified for first-time visitors: a clear introduction, one region/period selector, a large result and plain-language interpretation, followed by the map. History, baselines and technical evaluation expand on demand. Larger typography, native controls and mobile spacing replace the dense dashboard layout. Numerical forecasts and model settings are unchanged. The separate root reflection.txt contains the existing personally grounded 100-word English reflection. See READABILITY_REVIEW.json for checks and deployment status.
