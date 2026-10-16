"""Webhook authentication, routing and dependency-free deployment checks."""
import json
import io
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from alerts_forecast.pipeline import ROOT
from alerts_forecast.telegram_bot import command, ApiFailure
from alerts_forecast.telegram_webhook import dispatch, MAX_BODY, handler
from alerts_forecast import webhook_setup
from tools.build_bot_deployment import build

TEST_ENV = {'TELEGRAM_BOT_TOKEN': '123:EXAMPLE_TEST_TOKEN',
            'TELEGRAM_WEBHOOK_SECRET': 'example_test_secret_not_a_real_credential'}


class FakeAPI:
    calls = []

    def __init__(self, token, **kwargs):
        self.options = kwargs

    def call(self, method, payload):
        self.calls.append((method, payload))
        return True


class WebhookTests(unittest.TestCase):
    def setUp(self):
        FakeAPI.calls = []
        self.body = json.dumps({'update_id': 42, 'message': {
            'chat': {'id': 100, 'type': 'private'}, 'text': '/forecast Київ 3'}}).encode()

    def run_update(self, body=None, secret=None, factory=FakeAPI):
        with patch.dict(os.environ, TEST_ENV):
            return dispatch(self.body if body is None else body,
                            TEST_ENV['TELEGRAM_WEBHOOK_SECRET'] if secret is None else secret,
                            api_factory=factory)

    def test_correct_private_request_renders_shared_forecast(self):
        status, result = self.run_update()
        self.assertEqual(status, 200)
        self.assertTrue(result['ok'])
        self.assertEqual(FakeAPI.calls[0][0], 'sendMessage')
        self.assertIn('99,7%', FakeAPI.calls[0][1]['text'])

    def test_bad_or_missing_secret_sends_nothing(self):
        for supplied in ['', 'wrong-secret', 'неправильний']:
            self.assertEqual(self.run_update(secret=supplied)[0], 403)
        self.assertEqual(FakeAPI.calls, [])

    def test_unconfigured_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(dispatch(self.body, '')[0], 503)

    def test_bad_json_or_update_rejected(self):
        for bad in [b'{', b'[]', b'{}', b'{"update_id":true}']:
            self.assertEqual(self.run_update(body=bad)[0], 400)
        self.assertEqual(FakeAPI.calls, [])

    def test_body_size_bound(self):
        self.assertEqual(self.run_update(body=b'x' * (MAX_BODY + 1))[0], 413)

    def test_group_update_is_ignored(self):
        body = json.loads(self.body)
        body['message']['chat']['type'] = 'group'
        self.assertEqual(self.run_update(body=json.dumps(body).encode())[0], 200)
        self.assertEqual(FakeAPI.calls, [])

    def test_callback_buttons_use_existing_router(self):
        body = {'update_id': 43, 'callback_query': {'id': 'cb', 'data': 'f:UA-30:7',
                'message': {'chat': {'id': 100, 'type': 'private'}}}}
        self.assertEqual(self.run_update(body=json.dumps(body).encode())[0], 200)
        self.assertEqual([m for m, _ in FakeAPI.calls], ['answerCallbackQuery', 'sendMessage'])
        self.assertIn('2026-10-22', FakeAPI.calls[-1][1]['text'])

    def test_transport_failure_returns_retryable_status_without_details(self):
        class Broken(FakeAPI):
            def call(self, *_args):
                raise ApiFailure('sensitive-example-token-url')
        status, result = self.run_update(factory=Broken)
        self.assertEqual(status, 502)
        self.assertNotIn('sensitive', json.dumps(result))

    def test_webhook_transport_has_short_deadline_and_no_sleep(self):
        instances = []
        def factory(*args, **kwargs):
            item = FakeAPI(*args, **kwargs)
            instances.append(item)
            return item
        self.run_update(factory=factory)
        self.assertEqual(instances[0].options, {'timeout': 8, 'wait_on_rate_limit': False})

    def test_http_post_passes_secret_header_and_body_to_dispatch(self):
        request = handler.__new__(handler)
        request.headers = {'Content-Length': str(len(self.body)),
                           'X-Telegram-Bot-Api-Secret-Token': TEST_ENV['TELEGRAM_WEBHOOK_SECRET']}
        request.rfile = io.BytesIO(self.body)
        responses = []
        request.respond = lambda status, payload: responses.append((status, payload))
        def fake_dispatch(body, secret):
            return dispatch(body, secret, api_factory=FakeAPI)
        with patch.dict(os.environ, TEST_ENV), patch('alerts_forecast.telegram_webhook.dispatch', side_effect=fake_dispatch):
            request.do_POST()
        self.assertEqual(responses, [(200, {'ok': True})])
        self.assertEqual(FakeAPI.calls[0][0], 'sendMessage')


class SetupTests(unittest.TestCase):
    def test_registration_uses_secret_keeps_updates_and_checks_bot_identity(self):
        calls = []
        url = 'https://example.vercel.app/api/telegram'
        class SetupAPI:
            def __init__(self, _token): pass
            def call(self, method, payload):
                calls.append((method, payload))
                return {'getMe': {'username': 'air_alert_atlas_bot'},
                        'setWebhook': True, 'getWebhookInfo': {'url': url}}[method]
        with patch.dict(os.environ, TEST_ENV), patch.object(sys, 'argv', ['setup', '--url', url]), \
                patch('alerts_forecast.webhook_setup.urlopen', side_effect=[io.BytesIO(b'{"ok":true,"mode":"webhook"}'), io.BytesIO(b'{"ok":true}')]), \
                patch('alerts_forecast.webhook_setup.TelegramAPI', SetupAPI):
            webhook_setup.main()
        registration = next(payload for method, payload in calls if method == 'setWebhook')
        self.assertEqual(registration['secret_token'], TEST_ENV['TELEGRAM_WEBHOOK_SECRET'])
        self.assertFalse(registration['drop_pending_updates'])
        self.assertEqual(registration['allowed_updates'], ['message', 'callback_query'])

    def test_wrong_deployed_secret_does_not_change_telegram_routing(self):
        calls = []
        class SetupAPI:
            def __init__(self, _token): pass
            def call(self, method, payload):
                calls.append(method)
                return {'username': 'air_alert_atlas_bot'}
        with patch.dict(os.environ, TEST_ENV), patch.object(sys, 'argv', ['setup', '--url', 'https://example.vercel.app/api/telegram']), \
                patch('alerts_forecast.webhook_setup.urlopen', side_effect=[io.BytesIO(b'{"ok":true,"mode":"webhook"}'), OSError('example failure')]), \
                patch('alerts_forecast.webhook_setup.TelegramAPI', SetupAPI):
            with self.assertRaises(SystemExit):
                webhook_setup.main()
        self.assertEqual(calls, ['getMe'])

    def test_http_url_rejected_before_any_token_prompt_or_api_call(self):
        with patch.object(sys, 'argv', ['setup', '--url', 'http://example.com/api/telegram']), \
                patch('alerts_forecast.webhook_setup.getpass.getpass') as prompt:
            with self.assertRaises(SystemExit):
                webhook_setup.main()
            prompt.assert_not_called()


class DeploymentTests(unittest.TestCase):
    def test_entrypoint_declares_handler_for_static_deployment_discovery(self):
        build()
        entrypoint = ROOT / 'deploy/telegram/api/telegram.py'
        tree = ast.parse(entrypoint.read_text(encoding='utf-8'))
        declarations = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'handler']
        self.assertEqual(len(declarations), 1)
        result = subprocess.run([sys.executable, '-S', '-c',
            'from api.telegram import handler; from http.server import BaseHTTPRequestHandler; assert issubclass(handler, BaseHTTPRequestHandler); assert handler.__module__ == "api.telegram"'],
            cwd=ROOT / 'deploy/telegram', capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_uses_identical_outputs_for_every_region_and_horizon(self):
        build()
        package = json.loads((ROOT / 'deploy/telegram/site/data.json').read_text(encoding='utf-8'))
        original = json.loads((ROOT / 'site/data.json').read_text(encoding='utf-8'))
        for region in original['regions']:
            for horizon in [1, 3, 7]:
                for name in ['/forecast','/threshold']:
                    request = f'{name} {region["iso"]} {horizon}'
                    self.assertEqual(command(request, package), command(request, original))

    def test_deployment_imports_without_any_installed_packages(self):
        build()
        result = subprocess.run([sys.executable, '-S', '-c',
            'from api.telegram import handler; from alerts_forecast.telegram_webhook import forecast_data; assert len(forecast_data()["regions"])==27'],
            cwd=ROOT / 'deploy/telegram', capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
