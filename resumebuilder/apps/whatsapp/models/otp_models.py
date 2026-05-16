from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def otp_expiry():
    return timezone.now() + timedelta(minutes=10)


class OTPVerification(models.Model):

    VERIFY_CHOICES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('google-oauth2', 'Google'),
        ('linkedin-oauth2', 'LinkedIn'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    email_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    whatsapp_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    email_verified = models.BooleanField(default=False)

    whatsapp_verified = models.BooleanField(default=False)

    verified_via = models.CharField(
        max_length=20,
        choices=VERIFY_CHOICES,
        blank=True,
        null=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_completed = models.BooleanField(default=False)

    email_attempts = models.IntegerField(default=0)

    whatsapp_attempts = models.IntegerField(default=0)

    expires_at = models.DateTimeField(default=otp_expiry)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):

        if self.user:
            return self.user.username

        return "OTP Verification"