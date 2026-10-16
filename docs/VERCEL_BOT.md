# Run the Telegram bot without an open console

## Why closing the console stops it

The original bot uses long polling: a Python process on the owner's computer repeatedly asks Telegram for updates. Closing that console stops the process. Hiding its window would still require an awake, connected computer.

The prepared alternative is an HTTPS **webhook** on Vercel. Telegram sends each update to a short-lived Python function, which renders the same frozen forecast and sends a reply. It needs no permanent process, scheduled pings or model training in the cloud. The current public website stays unchanged; deploy the bot as a **second Vercel project** from the same repository.

Vercel documents a free Hobby plan for personal/noncommercial projects, with usage quotas. This small selection-stage demo is intended for that use, not unlimited traffic or guaranteed uptime. Check the current account/plan limits before deployment: [Hobby](https://vercel.com/docs/plans/hobby), [function limits](https://vercel.com/docs/functions/limitations), [Python runtime](https://vercel.com/docs/functions/runtimes/python). Hosting policies may change.

## 1. Generate and push the small deployment

From the repository root:

```powershell
./.venv/Scripts/python.exe tools/build_bot_deployment.py
```

Commit/push `deploy/telegram` together with the canonical Python changes. The normal README runner also regenerates it. This directory contains only standard-library Python code and compact forecast JSON, copied/generated from the main project. Do not edit its generated copies: edit `alerts_forecast/` or rebuild `site/data.json`, then regenerate. No tokens or ML dependencies are included.

For the prepared repository changes:

```powershell
git add README.md alerts_forecast tools tests docs deploy site
git commit -m "Add Vercel Telegram webhook deployment"
git push
```

## 2. Create the separate Vercel project

In Vercel choose **Add New → Project**, import the same GitHub repository, and set:

| Setting | Value |
| --- | --- |
| Root Directory | `deploy/telegram` |
| Framework Preset | Other |
| Build / Install command | No custom command; the included configuration sets both empty |
| Output Directory | Leave unset/default; do not enter `site` or `deploy/telegram` |

Do not change the root directory/settings of the existing dashboard project. The new project's root page may return 404; its real endpoint is **`/api/telegram`**.

Before deployment, add these **Production environment variables** in the new project's settings:

- `TELEGRAM_BOT_TOKEN`: the existing @air_alert_atlas_bot token, entered privately in Vercel.
- `TELEGRAM_WEBHOOK_SECRET`: a separate random secret, 16–256 letters/digits/underscores/hyphens. Keep the same value for the local registration step. Generate one locally, for example:

```powershell
./.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Do not send either value in chat or commit it. If variables are added after deployment, **redeploy** so the function receives them.

## 3. Verify configuration and connect Telegram once

Open `https://air-alert-atlas-bot-lilac.vercel.app/api/telegram` for the owner-created production deployment. For another deployment, substitute its own production domain. The endpoint should be publicly reachable and return `{"ok": true, "mode": "webhook"}`. A 503 means configuration is missing/invalid; a Vercel sign-in page means Telegram cannot reach it. GET readiness checks configuration only, not token validity or successful Telegram delivery. POST requests require the separate secret header.

Stop the old local polling bot with **Ctrl+C**. Do not run polling and webhook delivery together. From the main repository, run the following with the actual new URL:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.webhook_setup --url https://air-alert-atlas-bot-lilac.vercel.app/api/telegram
```

The script prompts for the existing bot token and webhook secret using hidden input (or reads the corresponding environment variables). Nothing is stored in files or command arguments. It checks deployed readiness, verifies the bot identity, and authenticates a message-free probe with the secret before changing Telegram routing. It then registers the URL/secret via `setWebhook` and verifies the registered URL. Pending updates are kept. This changes delivery for the existing bot; it does not create a new bot or username.

When registration finishes, **close the local console**. No local process needs to remain running in webhook mode.

## 4. Test with the console closed

In Telegram test `/start`, `/regions`, `/forecast Київ 3` and `/forecast Закарпатська 1`; press the inline 1/3/7-day buttons. Expected frozen results are unchanged: Kyiv/3 days is about 99.7% and 14.7 records, while Zakarpattia is unavailable. Ask another person to try the existing bot link. These live tests are needed before calling the cloud deployment verified.

If it fails, inspect the new Vercel project's function logs. Do not paste tokens, secret headers, incoming chat payloads or token-bearing API URLs into chat. Recheck the root directory, production environment, public endpoint and registration URL. Keep the previous local bot stopped while a webhook exists.

## Roll back to local polling

To remove the webhook safely, with hidden token input:

```powershell
./.venv/Scripts/python.exe -m alerts_forecast.webhook_setup --disable
./tools/run_bot.ps1
```

This returns to the original mode, which again requires an open process/awake computer. Webhook and polling are alternatives.

## Verification and limits

### If Vercel reports `[unused_function]` for `api/telegram.py`

The original generated entrypoint only imported `handler`. Python imported it successfully, but Vercel's static entrypoint detector did not recognize the file, so its `functions` pattern was left unmatched. The corrected generator emits an explicit top-level `class handler(_WebhookHandler)` inheriting the shared implementation.

This was reproduced with official `@vercel/python-analysis@0.15.0`: the import-only source returned no entrypoint, while the corrected source returned `handler`. See [VERCEL_DISCOVERY_FIX.json](VERCEL_DISCOVERY_FIX.json). The fix preserves authentication and rendering; removing the `functions` setting alone would not prove the endpoint was discovered.

Push the corrected `tools/build_bot_deployment.py`, generated `deploy/telegram/api/telegram.py`, tests and docs. Deploy the **newest commit**, not another build of the earlier failed commit. Keep Root Directory `deploy/telegram`, preset Other, and the existing private environment variables. A successful new cloud deployment still needs to be verified at `/api/telegram` before registration.

Official detector references: [Python entrypoint detection](https://github.com/vercel/vercel/blob/main/packages/fs-detectors/src/python.ts), [file-based Python functions](https://vercel.com/docs/functions/runtimes/python/api-directory).

Offline tests exercise secret-header rejection, malformed/oversized bodies, command/callback routing, retryable upstream failures and all 81 forecast responses. A separate Python process with site-packages disabled imports the deployment successfully, proving that pandas/sklearn are not required. These tests use fake Telegram transport and do not send real messages.

The owner deployed the webhook and completed hidden-input registration, then reported “Все працює” after the requested no-console test workflow. The assistant independently verified HTTP 200 and the readiness JSON at the production endpoint; it did not receive a token or operate a live Telegram session. This separates endpoint verification from owner-assisted delivery evidence. It does not establish continuous uptime or independently capture every command/button result.

The function waits for its Telegram calls before returning. It uses short timeouts and returns failure on transient errors so Telegram can retry. There is no durable deduplication store, so retries after partial failures can produce duplicate replies. Cold starts and free-tier limits can delay/unavailable replies; no 24/7 guarantee is claimed. Forecasts remain frozen and are not official alerts.

Telegram references: [webhooks](https://core.telegram.org/bots/webhooks), [setWebhook and secret_token](https://core.telegram.org/bots/api#setwebhook).
