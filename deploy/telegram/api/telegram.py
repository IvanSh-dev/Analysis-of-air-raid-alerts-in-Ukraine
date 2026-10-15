"""Generated Vercel entrypoint; canonical logic is in alerts_forecast/."""
from alerts_forecast.telegram_webhook import handler as _WebhookHandler


class handler(_WebhookHandler):
    """Declare the handler locally so Vercel static discovery can find it."""
    pass
