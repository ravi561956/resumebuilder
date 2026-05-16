from django.db import models


class SocialLoginSetting(models.Model):
    PROVIDER_CHOICES = (
        ('google-oauth2', 'Google'),
        ('linkedin-oauth2', 'LinkedIn'),
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        unique=True
    )
    client_id = models.TextField()
    client_secret = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.provider