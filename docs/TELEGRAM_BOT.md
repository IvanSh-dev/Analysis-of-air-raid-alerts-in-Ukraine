# Telegram bot

Registered public bot: [@air_alert_atlas_bot](https://t.me/air_alert_atlas_bot). Public dashboard: [Alert Atlas](https://analysis-of-air-raid-alerts-in-ukra.vercel.app/). The owner supplied the username; its public Telegram profile was verified on October 16, 2026.

The owner supplied live replies for `/forecast Київ 3` and `/forecast Закарпатська 1`. Both exactly matched local renderer output after whitespace normalization, including the Vercel map link. This is an owner-assisted manual check: the assistant had no token or authenticated Telegram session. See [TELEGRAM_MANUAL_CHECK.json](TELEGRAM_MANUAL_CHECK.json). Offline tests also passed. Two replies do not establish callback-button operation or 24/7 uptime. The static Vercel website does not run the Python process.

## Run the existing bot

This section describes local polling, which stops when its console closes. For independent cloud operation, use the prepared [Vercel webhook deployment](VERCEL_BOT.md) instead. Do not run both modes at once. The webhook has been tested offline but still needs the owner's Vercel deployment, private environment configuration and one-time registration.

Reproduce the project from the root README, then from the repository root in PowerShell:

```powershell
./tools/run_bot.ps1
```

Use the token for the already registered bot, retrieved privately from official [@BotFather](https://t.me/BotFather). The script reads it through hidden input, sets `TELEGRAM_BOT_TOKEN` for the process, and removes that variable if it was entered by the script. It does not save the token in a file, command argument or Git. Never paste it into this conversation.

Alternatively inject `TELEGRAM_BOT_TOKEN` with your secret manager and run:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.telegram_bot
```

Keep exactly one polling instance running. An existing webhook is reported, not deleted automatically. Stop with Ctrl+C. Restart after updating code or `site/data.json`; both are loaded by the running process. Continuous hosting is a separate decision, and 24/7 operation is not established.

## Commands and live check

- `/start` or `/regions`: territory buttons, including unsupported territories.
- `/forecast Київ 1`: Kyiv City, one day.
- `/forecast Київська 3`: Kyiv oblast, three days.
- `/forecast Харківська 7`: Kharkiv oblast, seven days.
- `/help`: event meaning and limitations.

The reply includes 1/3/7-day buttons. For the frozen example, `/forecast Київ 3` should show about 99.7%, 14.7 records and October 16–18; `/forecast Закарпатська 1` should say unavailable, never 0%. The map link should use the public Vercel address. Check these responses after restarting the updated bot.

The percentage means at least one archive record in the entire selected window, not an average daily probability or an official alert/danger estimate. Forecast origin: October 16, 2026 00:00 Europe/Kyiv; data version: October 15. This is not an automatically refreshed service or live alert feed.

## Offline verification and implementation

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.telegram_bot --dry-run "/forecast Київ 3"
./.venv/Scripts/python.exe -m pytest -q
```

Dry-run uses no token/network and sends nothing. Tests cover private command/callback routing, invalid periods, missing regions, Kyiv city/oblast separation, the public map link and token-safe errors. Fake transport tests are not live Telegram delivery.

The standard-library HTTPS implementation uses `getMe`, `getWebhookInfo`, `getUpdates`, `answerCallbackQuery` and `sendMessage`. It replies only to incoming private requests, without groups, broadcasts or automatic warnings. Only the last update offset is stored under ignored `.tmp/`; incoming chat text/IDs are not logged. Errors suppress token-bearing URLs. Exactly-once delivery after failures is not promised.

Official references: [Bot tutorial](https://core.telegram.org/bots/tutorial), [getUpdates](https://core.telegram.org/bots/api#getupdates), [sendMessage](https://core.telegram.org/bots/api#sendmessage). No additional Python dependency is needed.

## Current cloud delivery

The bot now uses the separate Vercel webhook at https://air-alert-atlas-bot-lilac.vercel.app/api/telegram. The owner confirmed working delivery after registration and the requested no-console test workflow. This is owner-assisted verification; individual new cloud replies and buttons were not independently captured. The assistant verified endpoint readiness without a token. Do not start local polling unless the webhook has first been disabled; see [the hosting guide](VERCEL_BOT.md).


## Two-event revision — October 16, 2026

The local revision adds `/threshold Київ 3` and event buttons alongside the existing `/forecast` event. The website has an explicit target selector; it updates probabilities, map, history, evaluation, AUC and the corresponding CSV. ≥3 includes exactly three on one local day, not the sum across days. The selected new-target method is smoothed frequency, chosen on validation. All counts still refer to all archive records. See [the experiment](THRESHOLD_PROBABILITY.md) and [integration verification](DUAL_TARGET_VERIFICATION.json). Both Vercel projects need the new commit; existing webhook registration remains valid. New-target live delivery is not yet verified.
