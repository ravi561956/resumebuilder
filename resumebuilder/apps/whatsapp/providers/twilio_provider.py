from twilio.rest import Client

from apps.whatsapp.models import WhatsAppSetting


class TwilioProvider:

    @staticmethod
    def send(phone, message):

        setting = WhatsAppSetting.objects.filter(
            provider='twilio',
            is_active=True
        ).first()

        if not setting:
            return False

        client = Client(
            setting.api_key,
            setting.access_token
        )

        response = client.messages.create(
            body=message,
            from_=f"whatsapp:{setting.whatsapp_number}",
            to=f"whatsapp:{phone}"
        )

        return response.sid