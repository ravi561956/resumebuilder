import requests
import json

from apps.whatsapp.models import WhatsAppSetting


class MetaProvider:

    @staticmethod
    def send(phone, message):

        setting = WhatsAppSetting.objects.filter(
            provider='meta',
            is_active=True
        ).first()

        if not setting:
            print("❌ No active Meta setting found")
            return False

        token = setting.access_token
        phone_number_id = setting.phone_number_id

        if not token:
            print("❌ Missing Meta token")
            return False

        if not phone_number_id:
            print("❌ Missing Phone Number ID")
            return False

        url = (
            f"https://graph.facebook.com/v25.0/"
            f"{phone_number_id}/messages"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # clean phone
        phone = str(phone)
        phone = phone.replace("+", "")
        phone = phone.replace(" ", "")

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

        print("META URL:", url)
        print("META PAYLOAD:", payload)

        try:

            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload)
            )

            print("META STATUS:", response.status_code)
            print("META RESPONSE:", response.text)

            if response.status_code == 200:
                return True

            return False

        except Exception as e:

            print("META ERROR:", str(e))
            return False