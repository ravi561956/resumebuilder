import requests
from openai import OpenAI
from django.core.exceptions import ValidationError
from django.conf import settings


def _value(provider, attr, default=''):
    return (getattr(provider, attr, '') or default).strip() if isinstance(getattr(provider, attr, default), str) else getattr(provider, attr, default)


def _openai_client(provider):
    kwargs = {'api_key': provider.api_key}
    if provider.base_url:
        kwargs['base_url'] = provider.base_url.rstrip('/')
    return OpenAI(**kwargs)


def generate_with_provider(provider, *, system_prompt, prompt, max_output_tokens):
    """Generate text with any configured provider and return output + usage metadata."""
    name = provider.name
    model = provider.model_name or {
        'openai': 'gpt-4o-mini',
        'deepseek': 'deepseek-chat',
        'grok': 'grok-3-mini',
        'anthropic': 'claude-3-5-haiku-latest',
        'gemini': 'gemini-2.0-flash',
        'azure_openai': 'gpt-4o-mini',
        'ollama': 'llama3.2',
    }.get(name, 'gpt-4o-mini')

    if not provider.api_key and name not in ('ollama',):
        raise ValidationError(f'{provider.get_name_display()} has no API key configured.')

    if name in ('openai', 'deepseek', 'grok'):
        if not provider.base_url:
            defaults = {
                'openai': 'https://api.openai.com/v1',
                'deepseek': 'https://api.deepseek.com/v1',
                'grok': 'https://api.x.ai/v1',
            }
            base_url = defaults[name]
        else:
            base_url = provider.base_url.rstrip('/')
        client = OpenAI(api_key=provider.api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=max_output_tokens,
            temperature=0.7,
        )
        output = (response.choices[0].message.content or '').strip()
        usage = getattr(response, 'usage', None)
        return output, {
            'input_tokens': int(getattr(usage, 'prompt_tokens', 0) or 0),
            'output_tokens': int(getattr(usage, 'completion_tokens', 0) or 0),
            'total_tokens': int(getattr(usage, 'total_tokens', 0) or 0),
        }

    if name == 'azure_openai':
        from openai import AzureOpenAI
        if not provider.base_url:
            raise ValidationError('Azure OpenAI requires Base URL (Azure endpoint).')
        client = AzureOpenAI(
            api_key=provider.api_key,
            azure_endpoint=provider.base_url.rstrip('/'),
            api_version=getattr(settings, 'AZURE_OPENAI_API_VERSION', '2024-10-21'),
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=max_output_tokens,
            temperature=0.7,
        )
        output = (response.choices[0].message.content or '').strip()
        usage = getattr(response, 'usage', None)
        return output, {
            'input_tokens': int(getattr(usage, 'prompt_tokens', 0) or 0),
            'output_tokens': int(getattr(usage, 'completion_tokens', 0) or 0),
            'total_tokens': int(getattr(usage, 'total_tokens', 0) or 0),
        }

    if name == 'gemini':
        endpoint = provider.base_url.rstrip('/') if provider.base_url else 'https://generativelanguage.googleapis.com/v1beta'
        url = f'{endpoint}/models/{model}:generateContent'
        response = requests.post(
            url,
            params={'key': provider.api_key},
            json={'systemInstruction': {'parts': [{'text': system_prompt}]}, 'contents': [{'role': 'user', 'parts': [{'text': prompt}]}], 'generationConfig': {'maxOutputTokens': max_output_tokens, 'temperature': 0.7}},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        output = ''.join(p.get('text', '') for p in data.get('candidates', [{}])[0].get('content', {}).get('parts', [])).strip()
        usage = data.get('usageMetadata', {})
        return output, {
            'input_tokens': int(usage.get('promptTokenCount', 0) or 0),
            'output_tokens': int(usage.get('candidatesTokenCount', 0) or 0),
            'total_tokens': int(usage.get('totalTokenCount', 0) or 0),
        }

    if name == 'anthropic':
        endpoint = provider.base_url.rstrip('/') if provider.base_url else 'https://api.anthropic.com/v1'
        response = requests.post(
            f'{endpoint}/messages',
            headers={'x-api-key': provider.api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
            json={'model': model, 'max_tokens': max_output_tokens, 'system': system_prompt, 'messages': [{'role': 'user', 'content': prompt}]},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        output = ''.join(block.get('text', '') for block in data.get('content', []) if block.get('type') == 'text').strip()
        usage = data.get('usage', {})
        return output, {
            'input_tokens': int(usage.get('input_tokens', 0) or 0),
            'output_tokens': int(usage.get('output_tokens', 0) or 0),
            'total_tokens': int((usage.get('input_tokens', 0) or 0) + (usage.get('output_tokens', 0) or 0)),
        }

    if name == 'ollama':
        endpoint = provider.base_url.rstrip('/') if provider.base_url else 'http://127.0.0.1:11434'
        response = requests.post(
            f'{endpoint}/api/chat',
            json={'model': model, 'stream': False, 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        output = (data.get('message', {}).get('content') or '').strip()
        return output, {
            'input_tokens': int(data.get('prompt_eval_count', 0) or 0),
            'output_tokens': int(data.get('eval_count', 0) or 0),
            'total_tokens': int((data.get('prompt_eval_count', 0) or 0) + (data.get('eval_count', 0) or 0)),
        }

    raise ValidationError(f'Unsupported AI provider: {provider.get_name_display()}')


def test_provider_connection(provider):
    output, usage = generate_with_provider(
        provider,
        system_prompt='You are a connectivity test assistant. Reply with exactly: CONNECTION_OK',
        prompt='Test the configured AI connection.',
        max_output_tokens=20,
    )
    if 'CONNECTION_OK' not in output:
        raise ValidationError(f'Provider responded, but the expected test response was not received. Response: {output[:120]}')
    return usage
