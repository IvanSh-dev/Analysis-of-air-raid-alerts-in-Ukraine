# Final review before Git push — October 16, 2026

Primary website: https://analysis-of-air-raid-alerts-in-ukra.vercel.app/
Registered bot: https://t.me/air_alert_atlas_bot

## Checked

| Check | Actual result |
| --- | --- |
| Public Vercel page and six static files | HTTP 200; deployed source/data matched the pre-review local files after normalizing Windows/Unix line endings |
| Live browser | Periods 1/3/7, count/probability controls, search, unavailable territory, evaluation/calibration switching and CSV download worked |
| Browser console | No error entries |
| Downloaded CSV | Matched local forecast CSV after line-ending normalization |
| Bot identity | Public Telegram page shows Alert Atlas / @air_alert_atlas_bot |
| Live bot command replies | Owner supplied replies for Kyiv/3 days and Zakarpattia/1 day; both exactly matched local output after whitespace normalization. No direct Telegram session/token was used by the assistant |
| Full README runner in the original repository | Exit code 0, 33 tests passed, all modelling/export steps executed |
| JavaScript | Syntax passed; minimal-DOM checks passed all 81 region/horizon states |
| Dependencies | `pip check`: no broken requirements |
| Source freshness | Current main still equals the pinned October 15 archive commit |

Machine-readable evidence: [FINAL_PUBLIC_CHECK.json](FINAL_PUBLIC_CHECK.json). Tests inspect feature and training-label availability, future revisions, missingness, chronological selection, probability-window events, bot routing and navigation. No ML settings or model choices were changed in this final review.

The changed local page was also served over HTTP and checked in the browser: the real Telegram button is present, the obsolete registration message is gone, and the diagnostic graph's accessibility label names the correct period. The browser console had no errors. This is local verification of the pending edits, separate from the already deployed Vercel version.

## Prepared changes

- Rewrote README in English with public website/bot links, reproduction instructions, actual metrics, coverage and evaluation limitations.
- Corrected the bot's map URL to Vercel and removed its private-site suffix.
- Replaced the website's obsolete “bot not registered” message with the real Telegram link and an honest process-availability note.
- Corrected the chart's accessibility label when viewing the exposed diagnostic period; added regression checks for the label and public navigation.
- Updated current hosting/bot documentation and prepared the English plain-text reflection. Historical execution/deployment evidence was retained as history rather than rewritten.

## Required after this review

The edits above are local. No GitHub commit, Git push, Vercel deployment or bot process restart was performed by this review. Push the reviewed changes using the existing Git workflow. If Vercel is connected to that branch, wait for its new deployment; otherwise redeploy the `site/` directory manually. Then confirm the Telegram section contains @air_alert_atlas_bot.

The owner-supplied replies already contain the public map link, so that running bot has picked up the correct URL. Restart only after further code/data changes, keeping one polling instance. A static Vercel deployment does not run this process.

The owner performed `/forecast Київ 3` and `/forecast Закарпатська 1` and pasted both live replies. Kyiv showed 99.7%, 14.7 records and October 16–18; Zakarpattia was unavailable rather than 0%. Full text matched the local renderer after whitespace normalization. See [TELEGRAM_MANUAL_CHECK.json](TELEGRAM_MANUAL_CHECK.json). Callback buttons and continuous uptime were not established by these two replies.

The latest mature target is October 13. Coverage remains 23/27 registry territories, with an archive-record proxy and assumed publication delay. The original test was already exposed, so there is no fresh independent test. These limitations are not repaired by hosting or better UI.

Refresh the authentic chat export after the final reply. The separate local `submission/` directory stays ignored by Git.

## No-console bot hosting — webhook prepared, not cloud-deployed

The owner reported that closing the polling console stops the bot and asked for a free alternative. Prepared a separate Vercel webhook project with the same canonical renderer and compact forecast data. Removed the bot runtime's unnecessary ML imports. Added secret-header authentication, bounded requests, short outbound timeouts, hidden-input registration with bot-identity and deployed-secret checks, and rollback to polling. No token was provided, no cloud project was created, no real Telegram API call was made, and no webhook was registered by the assistant.

The full README runner completed with 47 tests and unchanged model results; a final registration-probe regression brought the separately executed suite to 48 passing tests. All 81 UI states passed. The deployment imported with site-packages disabled and rendered all 81 region/horizon responses identically. Deployment instructions and free-plan limitations are in VERCEL_BOT.md; WEBHOOK_VERIFICATION.json records the boundary between offline checks and unperformed live deployment.

## Real Vercel deployment failure: import-only entrypoint — October 16, 2026

The owner reported `[unused_function]` for `api/telegram.py` during deployment. The initial local import/handler tests had passed, but did not cover Vercel static discovery. Checked the official Vercel detector and ran its published `@vercel/python-analysis@0.15.0` package against both source variants: import-only returned null; an explicit local handler class returned `handler`. Updated the generator and regenerated the entrypoint, preserving the shared implementation. Added a regression checking the actual local class declaration, module identity and BaseHTTPRequestHandler inheritance. All 49 Python tests passed. This verifies discovery with the official analyzer, not a successful cloud deployment; a new commit/deployment is still required. No secret, model or forecast changed.

## Readability revision and owner-confirmed cloud bot — October 16, 2026

The owner confirmed the Vercel bot works after the no-console registration workflow. Endpoint readiness was independently verified in the preceding conversation turn; no assistant Telegram session or credential sharing occurred. This supersedes earlier pending-deployment status entries. The website was then simplified for first-time visitors: a clear introduction, one region/period selector, a large result and plain-language interpretation, followed by the map. History, baselines and technical evaluation expand on demand. Larger typography, native controls and mobile spacing replace the dense dashboard layout. Numerical forecasts and model settings are unchanged. The separate root reflection.txt contains the existing personally grounded 100-word English reflection. See READABILITY_REVIEW.json for checks and deployment status.
