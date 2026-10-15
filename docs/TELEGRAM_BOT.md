# Telegram bot: ready code, not registered or running

The owner said no bot exists yet and requested code/instructions. The code and offline command/update handling tests were executed. No real Telegram API calls or messages were sent. A live end-to-end test requires the owner to create a bot and provide its token locally. The static website does not host this long-polling Python process.

## Create and run

1. In Telegram open the official [@BotFather](https://t.me/BotFather) and use `/newbot`. Choose its name/username and keep the returned token private. Registration is a human step; no username was reserved or invented by this project.
2. Reproduce the project using the root README. The generated `site/data.json` is the bot's forecast source.
3. From the repository root on Windows, run:

```powershell
./tools/run_bot.ps1
```

The script prompts for the token using hidden input, sets `TELEGRAM_BOT_TOKEN` for the process, then removes it if entered by the script. It does not write it to a file, command argument, chat or repository. Do not paste the token into this conversation. Alternatively set that environment variable using your secret manager and run:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.telegram_bot
```

4. Open your bot in Telegram and send `/start`, then choose a region and a 1/3/7-day period. Stop with Ctrl+C. Keep exactly one polling instance running. An active webhook is detected and reported; this code does not delete it automatically.

The bot is active only while that process is running. Continuous hosting is a separate deployment decision; the project does not claim 24/7 operation. It serves the frozen October 16 example, not new daily forecasts or live alerts. The Site URL is owner-private, so other bot users cannot automatically view it.

## Commands

* `/regions`: regional inline buttons, including unsupported territories.
* `/forecast Київ 1`: Kyiv City, one day.
* `/forecast Київська 3`: Kyiv oblast, three days.
* `/forecast Харківська 7`: Kharkiv oblast, seven days.
* `/help`: event meaning, source date and limitations.

Choosing a region defaults to one day; the result includes 1/3/7-day buttons. A probability refers to at least one archive record anywhere in the entire selected period, not a mean daily probability or official danger estimate. Missing territories do not return 0%.

## Offline verification

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.telegram_bot --dry-run "/forecast Київ 3"
./.venv/Scripts/python.exe -m pytest -q
```

Dry-run needs no token/network and sends nothing. Unit tests exercise private-command/callback dispatch with a fake transport, unsupported regions, invalid periods, city/oblast separation and token-safe errors. Actual Telegram delivery remains unverified until the bot is registered.

The implementation uses standard-library HTTPS and the official Bot API (`getMe`, `getWebhookInfo`, `getUpdates`, `answerCallbackQuery`, `sendMessage`). It responds only to incoming private commands/button presses: no groups, contact scraping, unsolicited broadcasts, subscription database or automatic warning service. Only the last update offset is stored under ignored `.tmp/`; incoming chat text/IDs are not logged. HTTPS errors are sanitized so the token-bearing API URL is not printed. Temporary failures back off; running a single instance and keeping its offset avoids ordinary repeated reads, although exactly-once message delivery is not promised after process/storage failures.

Official references checked October 15, 2026: [BotFather tutorial](https://core.telegram.org/bots/tutorial), [getUpdates](https://core.telegram.org/bots/api#getupdates), [sendMessage](https://core.telegram.org/bots/api#sendmessage). No additional Python dependency is required.
