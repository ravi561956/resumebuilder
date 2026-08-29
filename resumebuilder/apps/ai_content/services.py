from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from openai import OpenAI

from apps.moderation.models import AIProvider
from .models import AICreditBalance, AICreditTransaction, AIGeneration, AIContentSetting


def get_balance(user):
    balance, _ = AICreditBalance.objects.get_or_create(user=user)
    return balance


def get_generation_providers():
    providers = list(AIProvider.objects.filter(is_active=True).order_by('priority', 'id'))
    if not providers:
        raise ValidationError('No active AI provider is configured by the administrator.')
    return providers


def get_generation_provider():
    return get_generation_providers()[0]


def _client_for_provider(provider):
    from .provider_runtime import _openai_client
    return _openai_client(provider)

def generate_text(*, user, resume, feature, prompt, free=False, field_name='', max_output_tokens=None, require_ai_enabled=True):
    setting = AIContentSetting.get()
    if require_ai_enabled and not setting.ai_content_enabled:
        raise ValidationError('AI content generation is currently disabled by the administrator.')
    if not prompt.strip():
        raise ValidationError('Please provide enough information for the AI request.')

    providers = get_generation_providers()
    max_output_tokens = max_output_tokens or setting.max_output_tokens

    balance = get_balance(user)
    # Do not call an external provider when a paid request cannot possibly be charged.
    if not free and balance.available_tokens < setting.default_generation_cost:
        raise ValidationError(
            f'Insufficient AI credits. You need at least {setting.default_generation_cost:,} credits and have {balance.available_tokens:,} available.'
        )

    # Lock the balance while checking/charging.
    with transaction.atomic():
        balance = AICreditBalance.objects.select_for_update().get(pk=balance.pk)
        generation = AIGeneration.objects.create(
            user=user,
            resume=resume,
            feature=feature,
            field_name=field_name,
            prompt=prompt,
            is_free=free,
            status='processing',
        )
        try:
            last_error = None
            output = ''
            input_tokens = output_tokens = total_tokens = 0
            provider = None
            for candidate in providers:
                try:
                    from .provider_runtime import generate_with_provider
                    output, usage = generate_with_provider(
                        candidate,
                        system_prompt=setting.system_prompt,
                        prompt=prompt,
                        max_output_tokens=max_output_tokens,
                    )
                    provider = candidate
                    input_tokens = usage['input_tokens']
                    output_tokens = usage['output_tokens']
                    total_tokens = usage['total_tokens'] or (input_tokens + output_tokens)
                    if output:
                        break
                except Exception as provider_error:
                    last_error = provider_error
                    continue
            if provider is None:
                raise ValidationError(f'All active AI providers failed. Last error: {last_error}')
            if not output:
                raise ValidationError('The AI provider returned an empty response.')

            charged = 0 if free else (total_tokens or setting.default_generation_cost)
            if not free and balance.available_tokens < charged:
                raise ValidationError(
                    f'Insufficient AI credits. You need {charged:,} tokens and have {balance.available_tokens:,} available.'
                )

            if not free and charged:
                balance.used_tokens += charged
                balance.save(update_fields=['used_tokens', 'updated_at'])
                AICreditTransaction.objects.create(
                    user=user,
                    transaction_type='generation',
                    tokens=-charged,
                    description=f'{feature.replace("_", " ").title()} generation',
                )

            generation.output = output
            generation.input_tokens = input_tokens
            generation.output_tokens = output_tokens
            generation.total_tokens = total_tokens
            generation.charged_tokens = charged
            generation.is_free = free
            generation.status = 'success'
            generation.save(update_fields=['output', 'input_tokens', 'output_tokens', 'total_tokens', 'charged_tokens', 'is_free', 'status'])
            return generation
        except Exception as exc:
            generation.status = 'failed'
            generation.error_message = str(exc)
            generation.save(update_fields=['status', 'error_message'])
            raise


def credit_purchase(user, purchase):
    with transaction.atomic():
        balance, _ = AICreditBalance.objects.select_for_update().get_or_create(user=user)
        balance.purchased_tokens += purchase.tokens
        balance.save(update_fields=['purchased_tokens', 'updated_at'])
        AICreditTransaction.objects.create(
            user=user,
            transaction_type='purchase',
            tokens=purchase.tokens,
            description=f'Purchased {purchase.package.name}',
            purchase=purchase,
        )
