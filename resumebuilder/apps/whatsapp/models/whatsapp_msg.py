from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


class WhatsappMessage(models.Model):

    MESSAGE_TYPES = (
        ('welcome', 'Welcome Message'),
        ('confirmation', 'Confirmation Message'),
        ('otp', 'OTP Message'),
    )

    message_type = models.CharField(
        max_length=30,
        choices=MESSAGE_TYPES,
        unique=True
    )

    title = models.CharField(
        max_length=100
    )
    body = CKEditor5Field(
        'Whatsapp Message Body',
        config_name='default'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.get_message_type_display()