from django.contrib import admin
from .models import ModerationSetting, AIProvider
from django.contrib import admin
from .models import ModerationViolation



@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    list_display = (
        "name",
        "model_name",
        "is_active",
        "priority",
    )
    readonly_fields = ("test_connection",)

    @admin.display(description="Connection Test")
    def test_connection(self, obj):
        if not obj or not obj.pk:
            return "Save the provider first to test the connection."
        url = reverse("admin:moderation_aiprovider_test_connection", args=[obj.pk])
        return format_html('<a class="button" href="{}">Test Connection</a>', url)

    fieldsets = (
        ("Provider Configuration", {
            "fields": ("name", "is_active", "api_key", "test_connection", "model_name", "base_url", "priority"),
            "description": "Configure one or more providers. Multiple providers can be active; lower Priority values are tried first. Use Test Connection to validate each provider.",
        }),
    )


@admin.register(ModerationSetting)
class ModerationSettingAdmin(admin.ModelAdmin):

    list_display = (
        "moderation_enabled",
        "keyword_filter_enabled",
        "active_provider",
        "updated_at",
    )

    fieldsets = (
        (
            "Moderation Configuration",
            {
                "fields": (
                    "moderation_enabled",
                    "keyword_filter_enabled",
                    "active_provider",
                    "bad_keywords",
                )
            },
        ),
    )

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        if not request.user.is_superuser:
            return False

        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
# Provider connection testing is intentionally available only to Superadmins.
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.ai_content.provider_runtime import test_provider_connection


def _provider_test_url(obj):
    return f'../../{obj.pk}/test-connection/'

# Extend the already-registered AIProviderAdmin without creating another model/admin.
AIProviderAdmin._test_connection_link = lambda self, obj: format_html(
    '<a class="button" href="{}">Test Connection</a>', _provider_test_url(obj)
)
AIProviderAdmin._test_connection_link.short_description = 'Connection Test'
AIProviderAdmin.list_display = AIProviderAdmin.list_display + ('_test_connection_link',)

_original_get_urls = AIProviderAdmin.get_urls

def _get_urls(self):
    urls = _original_get_urls(self)
    custom = [
        path('<path:object_id>/test-connection/', self.admin_site.admin_view(self.test_connection_view), name='moderation_aiprovider_test_connection'),
    ]
    return custom + urls


def _test_connection_view(self, request, object_id):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    provider = self.get_object(request, object_id)
    if not provider:
        self.message_user(request, 'AI provider not found.', messages.ERROR)
        return redirect('..')
    try:
        usage = test_provider_connection(provider)
        self.message_user(
            request,
            f'✓ {provider.get_name_display()} connection successful. Model: {provider.model_name or "default"}. Test tokens: {usage.get("total_tokens", 0):,}.',
            messages.SUCCESS,
        )
    except Exception as exc:
        message = str(exc)
        if '429' in message or 'quota' in message.lower() or 'credit_balance_exhausted' in message.lower() or 'insufficient_quota' in message.lower():
            message = f'{provider.get_name_display()} API quota/credits are exhausted. Check the provider billing account.'
        self.message_user(request, f'✗ Connection failed: {message}', messages.ERROR)
    return redirect(f'../')

AIProviderAdmin.get_urls = _get_urls
AIProviderAdmin.test_connection_view = _test_connection_view
