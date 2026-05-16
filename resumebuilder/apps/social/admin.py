from django.contrib import admin

from apps.social.models.social_login_models import (
    SocialLoginSetting
)


@admin.register(SocialLoginSetting)
class SocialLoginSettingAdmin(admin.ModelAdmin):

    list_display = (
        'provider',
        'is_active',
        'created_at'
    )

    list_filter = (
        'provider',
        'is_active'
    )

    search_fields = (
        'provider',
    )