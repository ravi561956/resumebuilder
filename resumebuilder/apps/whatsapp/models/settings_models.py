from django.db import models

class WhatsAppSetting(models.Model):

    PROVIDER_CHOICES = (
        ('wireweb', 'WireWeb'),
        ('meta', 'Meta'),
        ('twilio', 'Twilio'),
        ('gupshup', 'Gupshup'),
    )

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default='wireweb'
    )

    api_key = models.TextField(blank=True, null=True)

    session_id = models.TextField(blank=True, null=True)

    access_token = models.TextField(blank=True, null=True)

    phone_number_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    app_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    enable_otp = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return self.provider