"""Generate a tiny, dependency-free Vercel bot project from canonical sources."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build():
    target = ROOT / 'deploy/telegram'
    (target / 'api').mkdir(parents=True, exist_ok=True)
    (target / 'alerts_forecast').mkdir(exist_ok=True)
    (target / 'site').mkdir(exist_ok=True)
    source = json.loads((ROOT / 'site/data.json').read_text(encoding='utf-8'))
    # Keep the identical forecast fields; map geometry/history are unnecessary here.
    data = {key: source[key] for key in ['forecastDate', 'dataVersion']}
    data['regions'] = [{key: region[key] for key in ['id', 'iso', 'name', 'reason', 'periods']}
                       for region in source['regions']]
    for region in data['regions']:
        region['periods'] = {h: {k: p[k] for k in ['end', 'probability', 'baselineProbability', 'count', 'countBaseline']}
                             for h, p in region['periods'].items()}
    (target / 'site/data.json').write_text(json.dumps(data, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    hashes = {}
    for name in ['__init__.py', 'telegram_bot.py', 'telegram_webhook.py']:
        src = ROOT / 'alerts_forecast' / name
        shutil.copy2(src, target / 'alerts_forecast' / name)
        hashes[name] = hashlib.sha256(src.read_bytes()).hexdigest()
    (target / 'api/telegram.py').write_text('"""Generated Vercel entrypoint; canonical logic is in alerts_forecast/."""\nfrom alerts_forecast.telegram_webhook import handler\n', encoding='utf-8')
    (target / 'requirements.txt').write_text('# Python standard library only; no ML runtime dependencies.\n', encoding='utf-8')
    (target / 'pyproject.toml').write_text('[project]\nname = "alert-atlas-webhook"\nversion = "0.1.0"\nrequires-python = ">=3.12"\ndependencies = []\n', encoding='utf-8')
    config = {'$schema': 'https://openapi.vercel.sh/vercel.json', 'framework': None,
              'installCommand': '', 'buildCommand': '',
              'functions': {'api/telegram.py': {'maxDuration': 30}}}
    (target / 'vercel.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    (target / 'GENERATED.json').write_text(json.dumps({'generator': 'tools/build_bot_deployment.py',
        'source_hashes': hashes, 'forecast_origin': data['forecastDate'],
        'data_version': data['dataVersion'], 'secrets_included': False}, indent=2) + '\n', encoding='utf-8')
    (target / 'README.md').write_text('# Generated Telegram webhook deployment\n\nVercel Root Directory: `deploy/telegram`; framework: Other; output directory: default/unset. Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` privately. Endpoint: `/api/telegram`.\n\nRead the [complete setup guide](../../docs/VERCEL_BOT.md). Rebuild from canonical sources using `python tools/build_bot_deployment.py`; do not edit generated Python/JSON copies. Cloud deployment and registration still require the owner.\n', encoding='utf-8')
    shutil.copy2(ROOT / 'LICENSE', target / 'LICENSE')
    shutil.copy2(ROOT / 'data/SOURCE_LICENSE', target / 'SOURCE_LICENSE')
    print('Generated deploy/telegram: stdlib-only webhook, shared renderer and compact forecast data.')


if __name__ == '__main__':
    build()
