from django.utils import timezone
from datetime import timedelta

from apps.whatsapp.models import OTPVerification

from apps.whatsapp.utils.otp import generate_otp

from apps.whatsapp.services.whatsapp_service import (
    WhatsAppService
)


class OTPService:

    @staticmethod
    def send_whatsapp_otp(user, phone):

        otp = generate_otp()

        otp_obj, created = (
            OTPVerification.objects.get_or_create(
                user=user
            )
        )

        # whatsapp otp
        otp_obj.whatsapp_otp = otp

        otp_obj.whatsapp_verified = False

        otp_obj.whatsapp_attempts = 0

        otp_obj.expires_at = (
            timezone.now() + timedelta(minutes=10)
        )

        # invalidate email otp
        otp_obj.email_otp = None

        otp_obj.email_verified = False

        otp_obj.save()

        print("SENDING OTP:", otp)
        print("PHONE:", phone)

        message = (
            f"Your Resume Builder OTP is {otp}. "
            f"Valid for 10 minutes."
        )

        response = WhatsAppService.send(
            phone,
            message
        )

        print("WHATSAPP RESPONSE:", response)

        return otp