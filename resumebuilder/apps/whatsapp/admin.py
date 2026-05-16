from django.contrib import admin
from .models import OTPVerification
from .models import WhatsAppSetting
from .models.whatsapp_msg import WhatsappMessage


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'email_verified',
        'whatsapp_verified',
        'verified_via',
        'is_completed',
        'verified_at'
    )


@admin.register(WhatsAppSetting)
class WhatsAppSettingAdmin(admin.ModelAdmin):

    list_display = (
        'provider',
        'is_active',
        'enable_otp'
    )
    
@admin.register(WhatsappMessage)
class WhatsappMessageAdmin(admin.ModelAdmin):

    list_display = (
        'message_type',
        'is_active',
        'updated_at'
    )

    search_fields = (
        'message_type',
        'title'
    )

    list_filter = (
        'message_type',
        'is_active'
    )