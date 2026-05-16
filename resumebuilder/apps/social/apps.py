from django.apps import AppConfig


class SocialConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'

    name = 'apps.social'

    verbose_name = 'Social Login Settings'

    def ready(self):

        from apps.social.utils import (
            load_social_credentials
        )

        load_social_credentials()