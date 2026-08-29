from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from .crypto import encrypt, decrypt


class PaymentGatewaySetting(models.Model):
    GATEWAY_CHOICES = (
        ('razorpay', 'Razorpay'),
    )
    MODE_CHOICES = (
        ('test', 'Test / Sandbox'),
        ('live', 'Live / Production'),
    )
    enabled = models.BooleanField(default=False)
    gateway = models.CharField(max_length=30, choices=GATEWAY_CHOICES, default='razorpay')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='test')
    # Stored encrypted in the database; values are transparently decrypted when
    # application code accesses the model. Existing plaintext values are migrated
    # lazily on save for backward compatibility.
    key_id = models.CharField(max_length=1000, blank=True)
    key_secret = models.CharField(max_length=1000, blank=True)
    webhook_secret = models.CharField(max_length=1000, blank=True)
    currency = models.CharField(max_length=3, default='INR')
    checkout_name = models.CharField(max_length=100, default='Resume Builder')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Gateway Setting'
        verbose_name_plural = 'Payment Gateway Setting'

    def save(self, *args, **kwargs):
        self.key_id = encrypt(self.key_id)
        self.key_secret = encrypt(self.key_secret)
        self.webhook_secret = encrypt(self.webhook_secret)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_gateway_display()} ({self.get_mode_display()})'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AIPackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tokens = models.PositiveIntegerField(help_text='AI credit/token balance added to the user after successful payment.')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price in INR.')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('display_order', 'price', 'id')

    def __str__(self):
        return f'{self.name} - {self.tokens:,} tokens - ₹{self.price}'


class AIContentSetting(models.Model):
    ai_content_enabled = models.BooleanField(default=True)
    paid_ai_required = models.BooleanField(default=True)
    default_generation_cost = models.PositiveIntegerField(
        default=500,
        help_text='Default credits charged for one AI content request when the exact API token usage is unavailable.'
    )
    max_output_tokens = models.PositiveIntegerField(default=800)
    system_prompt = models.TextField(
        blank=True,
        default=(
            'You are a professional resume and career-writing assistant. '
            'Write truthful, concise, ATS-friendly professional content. '
            'Never invent employers, qualifications, dates, metrics or achievements. '
            'Return only the requested content.'
        )
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI Content Setting'
        verbose_name_plural = 'AI Content Setting'

    def __str__(self):
        return 'AI Content Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class CoverLetterSetting(models.Model):
    enabled = models.BooleanField(default=True)
    free_for_users = models.BooleanField(
        default=True,
        help_text='When enabled, normal users can generate cover letters without consuming purchased AI credits.'
    )
    max_output_tokens = models.PositiveIntegerField(default=1000)
    prompt_template = models.TextField(
        blank=True,
        default=(
            'Create a tailored professional cover letter using the candidate resume and the supplied job description. '
            'Do not invent facts. Keep it concise and suitable for a job application.'
        )
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cover Letter Setting'
        verbose_name_plural = 'Cover Letter Setting'

    def __str__(self):
        return 'Cover Letter Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AICreditBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_credit_balance')
    purchased_tokens = models.PositiveBigIntegerField(default=0)
    used_tokens = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_tokens(self):
        return max(0, self.purchased_tokens - self.used_tokens)

    def __str__(self):
        return f'{self.user.username}: {self.available_tokens:,} available'


class AIPurchase(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_purchases')
    package = models.ForeignKey(AIPackage, on_delete=models.PROTECT, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    tokens = models.PositiveIntegerField()
    gateway = models.CharField(max_length=30, default='razorpay')
    gateway_order_id = models.CharField(max_length=150, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=150, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username} / {self.package.name} / {self.status}'


class AICreditTransaction(models.Model):
    TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('generation', 'Generation'),
        ('refund', 'Refund'),
        ('adjustment', 'Admin Adjustment'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_credit_transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    tokens = models.IntegerField(help_text='Positive adds credits; negative consumes credits.')
    description = models.CharField(max_length=255)
    purchase = models.ForeignKey(AIPurchase, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username}: {self.tokens:+,} ({self.transaction_type})'


class AIGeneration(models.Model):
    FEATURE_CHOICES = (
        ('resume_content', 'Resume Content'),
        ('cover_letter', 'Cover Letter'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_generations')
    resume = models.ForeignKey('resume.Resume', null=True, blank=True, on_delete=models.SET_NULL, related_name='ai_generations')
    feature = models.CharField(max_length=30, choices=FEATURE_CHOICES)
    field_name = models.CharField(max_length=100, blank=True)
    prompt = models.TextField()
    output = models.TextField(blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    charged_tokens = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username} / {self.feature} / {self.created_at:%Y-%m-%d %H:%M}'
