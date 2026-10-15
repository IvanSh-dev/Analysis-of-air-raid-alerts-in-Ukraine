# Dashboard: current probability/map version

Private hosted URL: https://ivan-alert-atlas-2026.mapledrum8.chatgpt.site

Updated successfully on October 16, 2026 Kyiv time. Audience remains owner-private; reviewers do not automatically have access. Local `site/index.html` is also usable without a hosted account. GitHub publication remains separate and has not been performed.

Exact Site, version, deployment and source-commit identifiers are in [SITE_V3_DEPLOYMENT.json](SITE_V3_DEPLOYMENT.json). The managed hosting checkout is separate from the Python/GitHub repository. Its tracked `.openai/hosting.json` retains the existing Site identity.

## Implemented

Ukrainian UI with real administrative geometry, 27 territorial entries and 23 supported forecasts per period; global 1/3/7-day controls; probability/count map modes; region click/search/sorting; explicit unavailable states; per-region historical probability graphs; validation/previously-exposed diagnostic switching; Brier/log-loss/reliability displays; data/source disclosures; Telegram setup status; CSV export. Site and bot read the same generated data. Python's `tools/build_dashboard.py` rebuilds `data.js`, `data.json` and `forecasts.csv`.

## Verification of this version

- Full README runner from the original user repository: exit code 0, 32 tests passed.
- Node syntax check and minimal-DOM logic tests: all 81 region/period states, joins, missing values, sorting and evaluation logic.
- Independent forecast/window audit and byte comparison: details in V3_VERIFICATION.json and ORIGINAL_CHECKOUT_VERIFICATION.json.
- Successful native Sites deployment of the packaged, pushed source; all six public files came from the verified original repository.
- Authenticated hosted desktop UI loaded actual data after explicit owner approval for ChatGPT profile sign-in.
- Switching 1 to 3 days changed the date range to October 16–18 and Kyiv's percentage to 99.7%, count to 14.7; seven days changed the end to October 22 and count mode updated the map heading/values.
- Selecting Zakarpattia on the map showed an unavailable forecast, the July 30 last record and an explicit statement that unknowns are not zero.
- Searching for Ivano-Frankivska returned one territory; selection showed 35.3% and 1.0 records for one day, matching generated data.
- The evaluation selector switched to the exposed diagnostic period, and the calibration tab changed its title/content for that period/horizon.
- Visually inspected the map in the actual hosted desktop page; hatched unavailable territories and selected-region detail were visible. Screenshot retained in the separate delivery outputs.
- Browser console error log was empty.

This iteration did not recheck mobile layout or the browser's CSV download. The generated CSV itself was checked byte-for-byte. Earlier browser checks in the count-version experiment do not substitute for these current checks. The dashboard has no automatic data updates, live warnings or danger estimates; the forecast origin remains frozen at October 16, 2026.
