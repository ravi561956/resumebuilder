from django.conf import settings


def load_social_credentials():

    try:
        from apps.social.models.social_login_models import (
            SocialLoginSetting
        )

        google = SocialLoginSetting.objects.filter(
            provider='google-oauth2',
            is_active=True
        ).first()

        if google:

            settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = (
                google.client_id
            )

            settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = (
                google.client_secret
            )

            print("GOOGLE CONFIG LOADED")

        linkedin = SocialLoginSetting.objects.filter(
            provider='linkedin-oauth2',
            is_active=True
        ).first()

        if linkedin:

            settings.SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = (
                linkedin.client_id
            )

            settings.SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = (
                linkedin.client_secret
            )

            print("LINKEDIN CONFIG LOADED")

    except Exception as e:

        print("SOCIAL CONFIG ERROR:", e)