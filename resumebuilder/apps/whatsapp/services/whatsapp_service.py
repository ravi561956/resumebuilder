from apps.whatsapp.models import WhatsAppSetting

from apps.whatsapp.providers.wireweb_provider import WireWebProvider
from apps.whatsapp.providers.meta_provider import MetaProvider
from apps.whatsapp.providers.twilio_provider import TwilioProvider
from apps.whatsapp.providers.gupshup_provider import GupshupProvider


class WhatsAppService:

    @staticmethod
    def send(phone, message):

        setting = WhatsAppSetting.objects.filter(
            is_active=True
        ).first()

        if not setting:
            return False

        provider = setting.provider

        if provider == "wireweb":
            return WireWebProvider.send(phone, message)

        elif provider == "meta":
            return MetaProvider.send(phone, message)

        elif provider == "twilio":
            return TwilioProvider.send(phone, message)

        elif provider == "gupshup":
            return GupshupProvider.send(phone, message)

        return False