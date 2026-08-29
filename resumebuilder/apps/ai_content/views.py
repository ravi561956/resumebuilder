import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from resume.models import Resume
from .forms import CoverLetterForm
from .models import AIPackage, AIPurchase, AIContentSetting, CoverLetterSetting
from .services import credit_purchase, generate_text, get_balance
from .payment import get_payment_gateway


def _resume_for_user(user):
    return get_object_or_404(Resume, user=user)


@login_required
def ai_dashboard(request):
    balance = get_balance(request.user)
    packages = AIPackage.objects.filter(is_active=True)
    ai_setting = AIContentSetting.get()
    cover_setting = CoverLetterSetting.get()
    purchases = AIPurchase.objects.filter(user=request.user)[:10]
    return render(request, 'ai_content/dashboard.html', {
        'balance': balance,
        'packages': packages,
        'ai_setting': ai_setting,
        'cover_setting': cover_setting,
        'purchases': purchases,
    })


@login_required
@require_POST
def create_order(request, package_id):
    package = get_object_or_404(AIPackage, id=package_id, is_active=True)
    if package.price <= Decimal('0.00'):
        return JsonResponse({'error': 'This package cannot be purchased online.'}, status=400)

    try:
        gateway = get_payment_gateway()
        if gateway['gateway'] != 'razorpay':
            raise ValidationError('The selected payment gateway is not supported yet.')
        key_id = gateway['key_id']
        key_secret = gateway['key_secret']
        import razorpay
        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create({
            'amount': int(package.price * 100),
            'currency': gateway['currency'],
            'receipt': f'ai-{request.user.id}-{package.id}-{timezone.now():%Y%m%d%H%M%S}',
            'notes': {'user_id': str(request.user.id), 'package_id': str(package.id)},
        })
    except Exception as exc:
        return JsonResponse({'error': f'Unable to create payment order: {exc}'}, status=502)

    purchase = AIPurchase.objects.create(
        user=request.user,
        package=package,
        amount=package.price,
        tokens=package.tokens,
        gateway_order_id=order['id'],
        status='created',
    )
    return JsonResponse({
        'key_id': key_id,
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'checkout_name': gateway['checkout_name'],
        'purchase_id': purchase.id,
        'package_name': package.name,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_email': request.user.email,
    })


@login_required
@require_POST
def verify_payment(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        purchase = get_object_or_404(AIPurchase, id=data.get('purchase_id'), user=request.user)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'Invalid payment response.'}, status=400)

    try:
        gateway = get_payment_gateway()
    except ValidationError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    if gateway['gateway'] != 'razorpay':
        return JsonResponse({'error': 'The selected payment gateway is not supported yet.'}, status=503)
    key_id = gateway['key_id']
    key_secret = gateway['key_secret']

    if data.get('razorpay_order_id') != purchase.gateway_order_id:
        return JsonResponse({'error': 'Payment order does not match the purchase.'}, status=400)

    try:
        import razorpay
        client = razorpay.Client(auth=(key_id, key_secret))
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature'],
        })
    except Exception:
        purchase.status = 'failed'
        purchase.save(update_fields=['status'])
        return JsonResponse({'error': 'Payment verification failed.'}, status=400)

    if purchase.status != 'paid':
        purchase.gateway_payment_id = data['razorpay_payment_id']
        purchase.gateway_signature = data['razorpay_signature']
        purchase.status = 'paid'
        purchase.paid_at = timezone.now()
        purchase.save(update_fields=['gateway_payment_id', 'gateway_signature', 'status', 'paid_at'])
        credit_purchase(request.user, purchase)

    return JsonResponse({'success': True, 'available_tokens': get_balance(request.user).available_tokens})


@login_required
@require_POST
def generate_resume_content(request):
    setting = AIContentSetting.get()
    if not setting.ai_content_enabled:
        return JsonResponse({'error': 'AI content is disabled by the administrator.'}, status=403)
    if setting.paid_ai_required and get_balance(request.user).available_tokens <= 0:
        return JsonResponse({'error': 'Please purchase an AI package before using AI resume content generation.'}, status=402)

    resume = _resume_for_user(request.user)
    field_name = request.POST.get('field_name', '').strip()
    instruction = request.POST.get('instruction', '').strip()
    allowed = {'short_desc', 'summary', 'skills', 'experience', 'education'}
    if field_name not in allowed:
        return JsonResponse({'error': 'AI generation is only available for supported resume content fields.'}, status=400)
    if not instruction:
        return JsonResponse({'error': 'Please describe what you want the AI to write.'}, status=400)

    current = getattr(resume, field_name, '') or ''
    prompt = (
        f'Resume section: {field_name}.\n'
        f'Candidate name: {resume.name}.\n'
        f'Current section content (use only as source material): {current}\n\n'
        f'Instruction: {instruction}'
    )
    try:
        generation = generate_text(
            user=request.user,
            resume=resume,
            feature='resume_content',
            field_name=field_name,
            prompt=prompt,
            free=not setting.paid_ai_required,
        )
    except (ValidationError, Exception) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return JsonResponse({
        'success': True,
        'content': generation.output,
        'charged_tokens': generation.charged_tokens,
        'available_tokens': get_balance(request.user).available_tokens,
    })


@require_POST
def razorpay_webhook(request):
    try:
        gateway = get_payment_gateway()
    except ValidationError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    if gateway['gateway'] != 'razorpay' or not gateway['webhook_secret']:
        return JsonResponse({'error': 'Razorpay webhook is not configured.'}, status=503)
    secret = gateway['webhook_secret']
    signature = request.headers.get('X-Razorpay-Signature', '')
    try:
        import razorpay
        client = razorpay.Client(auth=(gateway['key_id'], gateway['key_secret']))
        client.utility.verify_webhook_signature(request.body.decode('utf-8'), signature, secret)
        payload = json.loads(request.body.decode('utf-8'))
        payment = payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = payment.get('order_id')
        payment_id = payment.get('id')
        if not order_id:
            return JsonResponse({'ok': True})
        purchase = AIPurchase.objects.filter(gateway_order_id=order_id).first()
        if not purchase:
            return JsonResponse({'ok': True})
        if purchase.status != 'paid' and payload.get('event') in ('payment.captured', 'order.paid'):
            purchase.gateway_payment_id = payment_id or ''
            purchase.status = 'paid'
            purchase.paid_at = timezone.now()
            purchase.save(update_fields=['gateway_payment_id', 'status', 'paid_at'])
            credit_purchase(purchase.user, purchase)
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'error': 'Invalid webhook.'}, status=400)


@login_required
def cover_letter(request):
    setting = CoverLetterSetting.get()
    result = None
    if request.method == 'POST':
        if not setting.enabled:
            messages.error(request, 'Cover letter generation is currently disabled by the administrator.')
        else:
            form = CoverLetterForm(request.POST)
            if form.is_valid():
                if not setting.free_for_users and get_balance(request.user).available_tokens <= 0:
                    messages.error(request, 'Please purchase AI credits before generating a paid cover letter.')
                    return render(request, 'ai_content/cover_letter.html', {'form': form, 'setting': setting, 'result': None, 'balance': get_balance(request.user)})
                resume = _resume_for_user(request.user)
                data = form.cleaned_data
                prompt = (
                    f'{setting.prompt_template}\n\n'
                    f'Candidate resume:\nName: {resume.name}\nTitle: {resume.title}\nPosition: {resume.position}\n'
                    f'Summary: {resume.summary}\nSkills: {resume.skills}\nExperience: {resume.experience}\n'
                    f'Education: {resume.education}\n\n'
                    f'Job title: {data["job_title"]}\nCompany: {data["company_name"]}\n'
                    f'Job description:\n{data["job_description"]}\n\n'
                    f'Additional instructions:\n{data["additional_instructions"]}'
                )
                try:
                    result = generate_text(
                        user=request.user,
                        resume=resume,
                        feature='cover_letter',
                        prompt=prompt,
                        free=setting.free_for_users,
                        max_output_tokens=setting.max_output_tokens,
                        require_ai_enabled=False,
                    )
                except (ValidationError, Exception) as exc:
                    messages.error(request, str(exc))
    else:
        form = CoverLetterForm()
    return render(request, 'ai_content/cover_letter.html', {
        'form': form,
        'setting': setting,
        'result': result,
        'balance': get_balance(request.user),
    })

@login_required
@require_POST
def generate_component_content(request):
    """Generate AI content for any supported Resume Builder admin component."""
    from django.apps import apps
    from .component_config import AI_COMPONENT_FIELDS
    from resume.models import Resume

    model_name = request.POST.get('model', '').strip().lower()
    field_name = request.POST.get('field_name', '').strip()
    object_id = request.POST.get('object_id', '').strip()
    resume_id = request.POST.get('resume_id', '').strip()
    parent_model = request.POST.get('parent_model', '').strip().lower()
    parent_id = request.POST.get('parent_id', '').strip()
    current_content = request.POST.get('current_content', '').strip()
    instruction = request.POST.get('instruction', '').strip()

    allowed_fields = AI_COMPONENT_FIELDS.get(model_name)
    if not allowed_fields or field_name not in allowed_fields:
        return JsonResponse({'error': 'AI assistance is not enabled for this field.'}, status=400)
    if not instruction:
        return JsonResponse({'error': 'Please describe what you want the AI to write.'}, status=400)

    setting = AIContentSetting.get()
    if not setting.ai_content_enabled:
        return JsonResponse({'error': 'AI content generation is currently disabled by the administrator.'}, status=403)

    try:
        Model = apps.get_model('resume', model_name)
    except LookupError:
        return JsonResponse({'error': 'Unsupported AI component.'}, status=400)

    obj = None
    if object_id:
        obj = Model.objects.filter(pk=object_id).first()
        if not obj:
            return JsonResponse({'error': 'Component was not found.'}, status=404)

    # Resolve the Resume without trusting a user-supplied arbitrary object.
    from apps.moderation.services import _resolve_resume
    resume = _resolve_resume(obj) if obj is not None else None
    if resume_id:
        selected_resume = Resume.objects.filter(pk=resume_id).first()
        if selected_resume is not None:
            if resume is not None and resume.pk != selected_resume.pk:
                return JsonResponse({'error': 'Component does not belong to the selected resume.'}, status=403)
            resume = selected_resume
    if resume is None and model_name == 'resume' and obj is not None:
        resume = obj

    # On a new child form there is no child PK yet. Resolve its selected
    # parent (category/section/journey/etc.) so AI can still be used before save.
    if resume is None and parent_model and parent_id:
        try:
            Parent = apps.get_model('resume', parent_model)
            parent_obj = Parent.objects.filter(pk=parent_id).first()
            if parent_obj is not None:
                resume = _resolve_resume(parent_obj)
        except LookupError:
            pass

    if resume is None:
        # For a normal user's new form, their own resume is the safe fallback.
        resume = Resume.objects.filter(user=request.user).first()
    if resume is None:
        return JsonResponse({'error': 'Select or save a Resume before using AI assistance.'}, status=400)

    if not request.user.is_superuser and resume.user_id != request.user.id:
        return JsonResponse({'error': 'You do not have permission to use AI for this resume.'}, status=403)

    if obj is not None:
        resolved = _resolve_resume(obj)
        if resolved is not None and resolved.pk != resume.pk:
            return JsonResponse({'error': 'You do not have permission to use AI for this component.'}, status=403)

    if not current_content and obj is not None:
        current_content = str(getattr(obj, field_name, '') or '')

    context_lines = [
        f'Component: {Model._meta.verbose_name}',
        f'Field: {allowed_fields[field_name]}',
        f'Candidate name: {resume.name}',
        f'Resume title: {resume.title}',
        f'Professional position: {resume.position}',
    ]
    if current_content:
        context_lines.append(f'Current field content (source material only): {current_content}')
    prompt = '\n'.join(context_lines) + f'\n\nInstruction: {instruction}'

    try:
        generation = generate_text(
            user=request.user,
            resume=resume,
            feature='resume_content',
            field_name=f'{model_name}.{field_name}',
            prompt=prompt,
            free=not setting.paid_ai_required,
        )
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({
        'success': True,
        'content': generation.output,
        'charged_tokens': generation.charged_tokens,
        'available_tokens': get_balance(request.user).available_tokens,
    })
