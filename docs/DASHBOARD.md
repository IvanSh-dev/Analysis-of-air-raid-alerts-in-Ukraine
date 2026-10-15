# Public dashboard

Current primary URL: https://analysis-of-air-raid-alerts-in-ukra.vercel.app/
Telegram: https://t.me/air_alert_atlas_bot

The owner deployed the static dashboard to Vercel. On October 16, 2026, the public page loaded without authentication. HTML, CSS, JavaScript, JSON and CSV returned HTTP 200 and matched the pre-review local source after line-ending normalization. The browser passed period, map/count-mode, search, missingness, evaluation/calibration and CSV-download checks, with no console errors. See [FINAL_REVIEW.md](FINAL_REVIEW.md) and [FINAL_PUBLIC_CHECK.json](FINAL_PUBLIC_CHECK.json).

## Source and deployment

`site/` contains the complete static website. `tools/build_dashboard.py` regenerates `data.js`, `data.json` and `forecasts.csv` from executed Python results; the bot reads the same JSON. There are no Node dependencies, runtime map tiles or live backend. Preserve the existing Vercel settings; deploy the contents of `site/`. Python model training and Telegram polling run separately.

The current review updates the Telegram section and a chart accessibility label locally. These edits require a new Vercel deployment after Git push; the review does not claim to have deployed them. Map/probability data and model settings were unchanged.

The modified local page was served over HTTP and checked in the browser: the Telegram button and corrected diagnostic label are present, with no console errors.

The dashboard remains a fixed October 16 research example with 23 supported forecasts per period and four unavailable territories. It has no automatic refresh, danger probabilities or live warning service. Mobile layout was not rechecked in this final review.

## Historical hosting evidence

The earlier owner-private Sites deployment is retained as a historical experiment, not the primary demo. [SITE_V3_DEPLOYMENT.json](SITE_V3_DEPLOYMENT.json) records its exact old URL/commit/deployment and must not be rewritten to pretend Vercel was published by that operation. Earlier access settings do not describe the current public Vercel deployment. The old deployment records and earlier screenshots are provenance; all current navigation uses Vercel and the supplied bot username.
