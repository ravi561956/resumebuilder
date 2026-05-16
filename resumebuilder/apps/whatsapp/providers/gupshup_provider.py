import requests

from apps.whatsapp.models import WhatsAppSetting


class GupshupProvider:

    @staticmethod
    def send(phone, message):

        setting = WhatsAppSetting.objects.filter(
            provider='gupshup',
            is_active=True
        ).first()

        if not setting:
            return False

        url = "https://api.gupshup.io/sm/api/v1/msg"

        headers = {
            "apikey": setting.api_key
        }

        payload = {
            "channel": "whatsapp",
            "source": setting.whatsapp_number,
            "destination": phone,
            "message": message,
            "src.name": setting.app_name
        }

        response = requests.post(
            url,
            headers=headers,
            data=payload
        )

        return response.json()