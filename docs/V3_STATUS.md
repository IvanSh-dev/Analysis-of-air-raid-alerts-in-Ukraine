# Current delivery status

The complete Python project, static website, data and documentation are in `C:/Ivan/python/Analysis-of-air-raid-alerts-in-Ukraine/`. The owner committed/pushed the previous version and deployed the website publicly to https://analysis-of-air-raid-alerts-in-ukra.vercel.app/; the bot is registered at https://t.me/air_alert_atlas_bot. These facts supersede older “private site / bot not registered” status text.

The final review ran the full README in the original checkout successfully: 33 Python tests, model pipelines and dashboard export. JavaScript checks covered 81 states, live Vercel browser interactions passed, and the Telegram profile exists. Two live command replies supplied by the owner match expected output; this is a documented owner-assisted manual check, not independent direct Telegram observation by the assistant. See FINAL_REVIEW.md and FINAL_PUBLIC_CHECK.json.

Current review edits have not been committed/pushed or deployed by the assistant. After reviewing, push them through the existing Git/Vercel workflow and restart the Python bot only if its code/data changes further. The supplied live replies already use the public map link. The static site cannot keep the bot running.

Historical execution/deployment records remain factual history. The project still has 23 supported territories out of a 27-unit registry, a proxy target for archive records, assumed publication timing and no fresh independent test. It does not forecast official danger or replace official notifications.

## No-console bot hosting — webhook prepared, not cloud-deployed

The owner reported that closing the polling console stops the bot and asked for a free alternative. Prepared a separate Vercel webhook project with the same canonical renderer and compact forecast data. Removed the bot runtime's unnecessary ML imports. Added secret-header authentication, bounded requests, short outbound timeouts, hidden-input registration with bot-identity and deployed-secret checks, and rollback to polling. No token was provided, no cloud project was created, no real Telegram API call was made, and no webhook was registered by the assistant.

The full README runner completed with 47 tests and unchanged model results; a final registration-probe regression brought the separately executed suite to 48 passing tests. All 81 UI states passed. The deployment imported with site-packages disabled and rendered all 81 region/horizon responses identically. Deployment instructions and free-plan limitations are in VERCEL_BOT.md; WEBHOOK_VERIFICATION.json records the boundary between offline checks and unperformed live deployment.
