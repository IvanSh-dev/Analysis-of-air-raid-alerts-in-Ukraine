"""Short-lived, authenticated Telegram webhook; Python standard library only."""
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
import hmac
import json
import os
from pathlib import Path
import re

from .telegram_bot import TelegramAPI, ApiFailure, handle_update

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 1_000_000


@lru_cache(maxsize=1)
def forecast_data():
    return json.loads((ROOT / 'site/data.json').read_text(encoding='utf-8'))


def settings():
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET', '')
    if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+', token):
        return None
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,256}', secret):
        return None
    return token, secret


def dispatch(body, supplied_secret, api_factory=TelegramAPI):
    """Return status/body without exposing credentials, input text or user IDs."""
    config = settings()
    if config is None:
        return 503, {'ok': False, 'error': 'Webhook environment is not configured'}
    token, secret = config
    if not isinstance(supplied_secret, str) or not hmac.compare_digest(
            supplied_secret.encode('utf-8'), secret.encode('ascii')):
        return 403, {'ok': False, 'error': 'Forbidden'}
    if len(body) > MAX_BODY:
        return 413, {'ok': False, 'error': 'Payload too large'}
    try:
        update = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return 400, {'ok': False, 'error': 'Invalid JSON'}
    if not isinstance(update, dict) or type(update.get('update_id')) is not int:
        return 400, {'ok': False, 'error': 'Invalid update'}
    try:
        api = api_factory(token, timeout=8, wait_on_rate_limit=False)
        handle_update(update, forecast_data(), api)
    except (ApiFailure, OSError, ValueError, KeyError, TypeError):
        # Return failure so Telegram can retry; do not print a token-bearing URL.
        return 502, {'ok': False, 'error': 'Temporary processing failure'}
    return 200, {'ok': True}


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        # Never log headers, request text, chat identifiers or secrets.
        pass

    def respond(self, status, value):
        raw = json.dumps(value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        # Configuration/readiness only: not a guarantee of token validity or uptime.
        ready = settings() is not None
        self.respond(200 if ready else 503, {'ok': ready, 'mode': 'webhook'})

    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            size = -1
        if size < 0 or size > MAX_BODY:
            self.respond(413, {'ok': False, 'error': 'Invalid body size'})
            return
        status, value = dispatch(self.rfile.read(size), self.headers.get('X-Telegram-Bot-Api-Secret-Token', ''))
        self.respond(status, value)
