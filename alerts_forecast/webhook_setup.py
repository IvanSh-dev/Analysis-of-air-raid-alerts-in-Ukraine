"""Register a deployed webhook using hidden prompts, never token arguments."""
import argparse
import getpass
import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from .telegram_bot import TelegramAPI, ApiFailure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--url', help='Public HTTPS endpoint ending /api/telegram')
    mode.add_argument('--disable', action='store_true', help='Remove webhook to return to local polling; keeps pending updates')
    args = parser.parse_args()
    address = urlparse(args.url or '')
    if not args.disable and (address.scheme != 'https' or not address.hostname or address.username or address.password
            or address.query or address.fragment or address.path != '/api/telegram'):
        parser.error('Use the deployed public HTTPS URL ending /api/telegram, without credentials/query/fragment')
    if not args.disable:
        try:
            with urlopen(args.url, timeout=15) as response:
                health = json.load(response)
            if not health.get('ok') or health.get('mode') != 'webhook':
                parser.exit(1, 'Webhook readiness failed; check Vercel environment and deployment.\n')
        except Exception:
            parser.exit(1, 'Cannot reach a ready public webhook. Check deployment protection and environment, then redeploy.\n')
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or getpass.getpass('Bot token (hidden, not saved): ')
    try:
        api = TelegramAPI(token)
        identity = api.call('getMe', {})
        if identity.get('username', '').casefold() != 'air_alert_atlas_bot':
            parser.exit(1, 'Token belongs to a different bot; nothing changed.\n')
        if args.disable:
            api.call('deleteWebhook', {'drop_pending_updates': False})
            if api.call('getWebhookInfo', {}).get('url'):
                parser.exit(1, 'Webhook removal verification failed.\n')
            print('Webhook removed. You may run tools/run_bot.ps1 again; computer must remain on.')
            return
        secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET') or getpass.getpass('Webhook secret from Vercel (hidden, not saved): ')
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{16,256}', secret):
            parser.exit(1, 'Webhook secret must contain 16-256 letters, digits, underscores or hyphens.\n')
        # Authenticate against the deployed endpoint before changing Telegram routing.
        # An update with no message/callback is ignored and sends no chat messages.
        probe = Request(args.url, data=b'{"update_id":-1}', method='POST', headers={
            'Content-Type': 'application/json', 'X-Telegram-Bot-Api-Secret-Token': secret})
        try:
            with urlopen(probe, timeout=15) as response:
                accepted = json.load(response)
            if not accepted.get('ok'):
                parser.exit(1, 'Webhook authentication failed; Telegram routing was not changed.\n')
        except Exception:
            parser.exit(1, 'Webhook secret/endpoint check failed; Telegram routing was not changed.\n')
        api.call('setWebhook', {'url': args.url, 'secret_token': secret,
            'allowed_updates': ['message', 'callback_query'], 'max_connections': 1,
            'drop_pending_updates': False})
        state = api.call('getWebhookInfo', {})
        if state.get('url') != args.url:
            parser.exit(1, 'Webhook URL verification failed.\n')
        print('Webhook registered for @air_alert_atlas_bot. Close the local console and test two commands plus inline buttons.')
        print('Pending updates:', state.get('pending_update_count', 0))
    except ApiFailure as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
