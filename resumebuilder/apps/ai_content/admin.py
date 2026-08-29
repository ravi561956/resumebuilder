from django.conf import settings
from django.contrib import admin
from django import forms
from django.utils import timezone

from .models import (
    AIPackage, AIContentSetting, CoverLetterSetting, AICreditBalance,
    PaymentGatewaySetting,
    AIPurchase, AICreditTransaction, AIGeneration,
)
from .services import credit_purchase


class PaymentGatewaySettingForm(forms.ModelForm):
    key_id = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False), help_text='Leave blank when editing to keep the current encrypted value.')
    key_secret = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False), help_text='Leave blank when editing to keep the current encrypted value.')
    webhook_secret = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False), help_text='Leave blank when editing to keep the current encrypted value.')

    class Meta:
        model = PaymentGatewaySetting
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        if self.instance and self.instance.pk:
            for field in ('key_id', 'key_secret', 'webhook_secret'):
                if cleaned.get(field) == '':
                    cleaned[field] = getattr(self.instance, field)
        return cleaned

    def clean_mode(self):
        mode = self.cleaned_data.get('mode')
        if mode == 'live' and getattr(settings, 'DEBUG', False):
            raise forms.ValidationError('Live/Production mode is blocked while DEBUG=True. Use Test/Sandbox mode during development.')
        return mode


class SuperAdminOnlyMixin:
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


@admin.register(PaymentGatewaySetting)
class PaymentGatewaySettingAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    form = PaymentGatewaySettingForm
    list_display = ('gateway', 'mode', 'enabled', 'currency', 'updated_at')
    fieldsets = (
        ('Gateway', {
            'fields': ('enabled', 'gateway', 'mode', 'currency', 'checkout_name'),
            'description': 'Configure payment gateway credentials here. Use Test/Sandbox credentials during development and Live credentials only in production.',
        }),
        ('Credentials', {
            'fields': ('key_id', 'key_secret', 'webhook_secret'),
            'description': 'For Razorpay, enter the Key ID, Key Secret and optional Webhook Secret from the Razorpay dashboard.',
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return request.user.is_superuser and not PaymentGatewaySetting.objects.exists()



@admin.register(AIPackage)
class AIPackageAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('name', 'tokens', 'price', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'price')


@admin.register(AIContentSetting)
class AIContentSettingAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('ai_content_enabled', 'paid_ai_required', 'default_generation_cost', 'max_output_tokens', 'updated_at')

    def has_add_permission(self, request):
        return request.user.is_superuser and not AIContentSetting.objects.exists()


@admin.register(CoverLetterSetting)
class CoverLetterSettingAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('enabled', 'free_for_users', 'max_output_tokens', 'updated_at')

    def has_add_permission(self, request):
        return request.user.is_superuser and not CoverLetterSetting.objects.exists()


@admin.register(AICreditBalance)
class AICreditBalanceAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('user', 'purchased_tokens', 'used_tokens', 'available')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'used_tokens', 'updated_at')

    @admin.display(description='Available')
    def available(self, obj):
        return obj.available_tokens


@admin.register(AIPurchase)
class AIPurchaseAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('user', 'package', 'amount', 'tokens', 'status', 'gateway_order_id', 'paid_at', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('user__username', 'user__email', 'gateway_order_id', 'gateway_payment_id')
    readonly_fields = (
        'amount', 'currency', 'tokens', 'gateway', 'gateway_order_id',
        'gateway_payment_id', 'gateway_signature', 'paid_at', 'created_at',
    )

    def save_model(self, request, obj, form, change):
        # A purchase created manually by a superadmin is a developer/test
        # purchase. The package is the source of truth for price and credits.
        if not change:
            if not obj.package_id:
                raise ValueError('Select an AI package before saving the purchase.')

            package = obj.package
            obj.amount = package.price
            obj.tokens = package.tokens
            obj.currency = 'INR'

            # Never create a fake payment in production. In local development,
            # admin-created purchases are automatically marked paid so the
            # complete credit flow can be tested without Razorpay.
            if getattr(settings, 'DEBUG', False):
                obj.gateway = 'development'
                obj.status = 'paid'
                obj.paid_at = timezone.now()
            else:
                obj.gateway = 'razorpay'
                obj.status = 'created'

        was_new = not change
        super().save_model(request, obj, form, change)

        if was_new and obj.status == 'paid':
            credit_purchase(obj.user, obj)


@admin.register(AICreditTransaction)
class AICreditTransactionAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'tokens', 'description', 'purchase', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = [f.name for f in AICreditTransaction._meta.fields]


@admin.register(AIGeneration)
class AIGenerationAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('user', 'feature', 'field_name', 'total_tokens', 'charged_tokens', 'is_free', 'status', 'created_at')
    list_filter = ('feature', 'status', 'is_free', 'created_at')
    search_fields = ('user__username', 'user__email', 'field_name')
    readonly_fields = [f.name for f in AIGeneration._meta.fields]
