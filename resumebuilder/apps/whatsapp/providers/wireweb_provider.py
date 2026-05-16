import requests

from apps.whatsapp.models import WhatsAppSetting


class WireWebProvider:

    @staticmethod
    def send(phone, message):

        setting = WhatsAppSetting.objects.filter(
            is_active=True
        ).first()

        if not setting:
            return False

        url = "https://api.wireweb.co.in/v1/messages/send"

        payload = {
            "session_id": setting.session_id,
            "to": phone,
            "type": "text",
            "message": message
        }

        headers = {
            "X-API-Key": setting.api_key
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers
        )

        return response.json()