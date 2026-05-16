from django.contrib.auth.models import User, Group
from resume.models import Resume
from apps.whatsapp.models.otp_models import OTPVerification
from resume.views import send_welcome_email
from django.utils import timezone
import threading


def create_social_user(
    strategy,
    details,
    backend,
    user=None,
    *args,
    **kwargs
):

    # already logged in
    if user:
        return {
            'user': user
        }
    email = details.get('email')

    first_name = details.get('first_name', '')

    last_name = details.get('last_name', '')

    fullname = (
        f"{first_name} {last_name}"
    ).strip()

    # username from email
    username = email.split('@')[0]

    # make unique username
    original_username = username

    counter = 1

    while User.objects.filter(
        username=username
    ).exists():

        username = (
            f"{original_username}{counter}"
        )

        counter += 1

    # create user
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password="G1!a@2r3#@123$3$2#"
    )

    # social users auto verified
    user.is_active = True
    # allow admin access
    user.is_staff = True
    # add editor group
    group, _ = Group.objects.get_or_create(
        name="Resume Editor"
    )
    user.groups.add(group)
    user.save()
    
    # create unique subdomain
    subdomain = username.lower()

    counter = 1

    while Resume.objects.filter(
        subdomain=subdomain
    ).exists():

        subdomain = (
            f"{username.lower()}{counter}"
        )
        counter += 1

    # phone if available
    phone = ''

    # GOOGLE
    if backend.name == 'google-oauth2':
        phone = ''

    # LINKEDIN
    elif backend.name == 'linkedin-oauth2':
        phone = ''

    # create resume
    Resume.objects.create(
        user=user,
        subdomain=subdomain,
        name=fullname or username,
        title='My Resume',
        email=email,
        phone=phone,
        theme='Style',
        is_active=True
    )

    print("backend", backend.name)
    # mark verified
    OTPVerification.objects.create(
        user=user,
        email_verified=True,
        whatsapp_verified=False,
        verified_via=backend.name,
        verified_at=timezone.now(),
        is_completed=True
    )
    threading.Thread(
        target=send_welcome_email,
        args=(user,),
        daemon=True
    ).start()
    return {
        'user': user
    }