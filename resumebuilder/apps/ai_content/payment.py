from django.conf import settings
from django.core.exceptions import ValidationError
from .models import PaymentGatewaySetting
from .crypto import decrypt


def get_payment_gateway():
    """Return the DB-configured gateway, falling back to environment settings.

    Superadmin configuration is the preferred source. Environment variables are
    retained as a safe migration/fallback path for existing installations.
    """
    config = PaymentGatewaySetting.get()
    if config.enabled and config.gateway == 'razorpay':
        if config.mode == 'live' and getattr(settings, 'DEBUG', False):
            raise ValidationError('Live payment mode is blocked while DEBUG=True. Use Razorpay Test/Sandbox mode for development.')
        key_id = decrypt(config.key_id)
        key_secret = decrypt(config.key_secret)
        webhook_secret = decrypt(config.webhook_secret)
        if not key_id or not key_secret:
            raise ValidationError('Razorpay is enabled but Key ID or Key Secret is missing.')
        return {
            'gateway': 'razorpay',
            'mode': config.mode,
            'key_id': key_id,
            'key_secret': key_secret,
            'webhook_secret': webhook_secret,
            'currency': config.currency or 'INR',
            'checkout_name': config.checkout_name or 'Resume Builder',
        }

    # Existing .env configuration remains usable until the superadmin enables
    # a database gateway configuration.
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    if key_id and key_secret:
        return {
            'gateway': 'razorpay',
            'mode': 'test' if getattr(settings, 'DEBUG', False) else 'live',
            'key_id': key_id,
            'key_secret': key_secret,
            'webhook_secret': getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', ''),
            'currency': 'INR',
            'checkout_name': 'Resume Builder',
        }
    raise ValidationError('Payment gateway is not configured by the administrator.')
