import random
import threading
from datetime import timedelta
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404, FileResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Resume, ContactSection
from .forms import RegisterForm, ResumeForm, ContactForm, UserLoginForm
# ✅ Correct imports (cleaned)
from .utils.session_utils import get_user_sessions, delete_user_sessions
from .utils.resume_pdf import generate_resume_pdf
from .utils.resume_docx import generate_resume_docx
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.http import HttpResponse
from apps.whatsapp.models.otp_models import OTPVerification
from django.utils import timezone
from apps.whatsapp.utils.message_helper import get_whatsapp_message
from apps.whatsapp.services.whatsapp_service import (
    WhatsAppService
)
from apps.whatsapp.utils.otp import generate_otp
from django.db import IntegrityError

    
# ✅ Define async email sender
def send_otp_email(otp, user):
    subject = "Your OTP Code"
    text_content = render_to_string("auth/otp/otp.txt", {
        "otp": otp,
        "user": user
    })
    html_content = render_to_string("auth/otp/otp.html", {
        "otp": otp,
        "user": user
    })
    email = EmailMultiAlternatives(
        subject,
        text_content,
        "no-reply@resumebuilder.com",
        [user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def send_welcome_email(user):
    
    subject = "Welcome to Resume Builder"

    text_content = render_to_string(
        "auth/welcome/welcome_email.txt",
        {
            "user": user
        }
    )

    html_content = render_to_string(
        "auth/welcome/welcome_email.html",
        {
            "user": user
        }
    )

    email = EmailMultiAlternatives(
        subject,
        text_content,
        "no-reply@resumebuilder.com",
        [user.email],
    )

    email.attach_alternative(html_content, "text/html")

    email.send()


def send_registration_whatsapp_message(
    user,
    phone=None
):

    # fallback phone from resume
    if not phone:

        try:
            resume = Resume.objects.get(
                user=user
            )

            phone = resume.phone

        except Resume.DoesNotExist:
            return False

    # clean phone
    phone = str(phone)

    phone = phone.replace("+", "")
    phone = phone.replace(" ", "")

    if not phone.startswith("91"):
        phone = "91" + phone

    # message OUTSIDE if block
    message = get_whatsapp_message(
        "welcome",
        {
            "username": user.username,
            "email": user.email,
        }
    )

    if not message:
        return False

    return WhatsAppService.send(
        phone,
        message
    )

   
def send_verified_whatsapp_message(
    user,
    phone
):

    try:

        resume = Resume.objects.get(
            user=user
        )

        subdomain_url = (
            f"http://{resume.subdomain}.lvh.me:8000"
        )

    except Resume.DoesNotExist:

        subdomain_url = "Profile not available"

    message = get_whatsapp_message(
        "confirmation",
        {
            "username": user.username,
            "resume_url": subdomain_url,
        }
    )

    WhatsAppService.send(
        phone,
        message
    )
# -------------------------
# COMMON: Get resume by subdomain
# -------------------------


def get_resume(request):
    host = request.get_host().split(':')[0].lower()

    print("HOST:", host)  # DEBUG

    # Handle lvh.me (local subdomain)
    if host.endswith("lvh.me"):
        parts = host.split('.')

        # ranjan.lvh.me
        if len(parts) >= 3:
            subdomain = parts[0]
            print("SUBDOMAIN:", subdomain)

            return Resume.objects.filter(
                subdomain=subdomain,
                is_active=True
            ).first()

    # No subdomain case
    return None


# -------------------------
# LANDING PAGE (FIXED)
# -------------------------
def landing(request):
    resume = get_resume(request)

    # ✅ If subdomain resume exists
    if resume:
        print(resume.theme)
        template_name = f"themes/{resume.theme}/index.html"
        fallback = "themes/default/index.html"

        try:
            return render(request, template_name, {"resume": resume})
        except TemplateDoesNotExist:
            return render(request, fallback, {"resume": resume})

    # ✅ MAIN DOMAIN (IMPORTANT FIX)
    host = request.get_host().split(':')[0]

    if host in ["127.0.0.1", "localhost", "lvh.me"]:
        return render(request, "landing.html")   # 👈 main landing page

    # ❌ Subdomain but no resume
    return render(request, "themes/no_resume.html")


# -------------------------
# REGISTER
# -------------------------
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = email.split("@")[0]
            password = form.cleaned_data['password']
            subdomain = form.cleaned_data['subdomain']
            phone = form.cleaned_data['phone']
            # check subdomain first
            if Resume.objects.filter(subdomain=subdomain).exists():

                messages.error(
                    request,
                    "Subdomain already taken"
                )
                return redirect('register')
            try:
                # CREATE DJANGO USER
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False
                )
                user.save()

                # CREATE RESUME
                Resume.objects.create(
                    user=user,
                    subdomain=subdomain,
                    name=username,
                    title="My Resume",
                    email=email,
                    theme='Style',
                    phone=phone
                )
            except IntegrityError:
                messages.error(
                    request,
                    "Username or email already exists."
                )
                return redirect('register')
                             
            email_otp = str(
                random.randint(100000, 999999)
            )

            whatsapp_otp = str(
                random.randint(100000, 999999)
            )

            OTPVerification.objects.filter(
                user=user
            ).delete()

            OTPVerification.objects.create(
                user=user,

                email_otp=email_otp,
                whatsapp_otp=whatsapp_otp,

                email_verified=False,
                whatsapp_verified=False,
            )

            request.session['user_id'] = user.id

            request.session.modified = True

            # send email otp
            threading.Thread(
                target=send_otp_email,
                args=(email_otp, user),
                daemon=True
            ).start()

            # phone format
            phone = str(
                form.cleaned_data['phone']
            )

            phone = phone.replace("+", "")
            phone = phone.replace(" ", "")

            if not phone.startswith("91"):
                phone = "91" + phone

            print("PHONE:", phone)
            
            # send welcome company message
            threading.Thread(
                target=send_registration_whatsapp_message,
                args=(user, phone),
                daemon=True
            ).start()
            
            # send whatsapp otp
            otp_message = get_whatsapp_message(
                "otp",
                {
                    "username": user.username,
                    "otp": whatsapp_otp,
                    "email": user.email,
                }
            )

            if otp_message:

                threading.Thread(
                    target=WhatsAppService.send,
                    args=(phone, otp_message),
                    daemon=True
                ).start()
            messages.success(
                request,
                "OTP sent to Email and WhatsApp."
            )

            return redirect('verify_otp')

    else:

        form = RegisterForm()

    return render(
        request,
        "register.html",
        {
            "form": form
        }
    )


# -------------------------
# OTP VERIFY
# -------------------------
@never_cache
@csrf_protect
@never_cache
def verify_otp(request):

    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Your session expired.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        otp_obj = OTPVerification.objects.get(user=user)

    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        messages.error(request, "OTP session expired.")
        return redirect('register')

    if request.method == "POST":

        entered_otp = request.POST.get('otp', '').strip()

        # check expiry
        if timezone.now() > otp_obj.expires_at:

            otp_obj.delete()

            messages.error(
                request,
                "OTP expired. Please request a new one."
            )

            return redirect('resend_otp')

        # invalid otp
        if (
            entered_otp != otp_obj.email_otp and
            entered_otp != otp_obj.whatsapp_otp
        ):

            otp_obj.email_attempts += 1
            otp_obj.whatsapp_attempts += 1

            otp_obj.save()
            messages.error(
                request,
                "Invalid OTP"
            )

            return redirect('verify_otp')

        # SUCCESS
        user.is_active = True
        user.is_staff = True
        group, _ = Group.objects.get_or_create(
            name="Resume Editor"
        )
        user.groups.add(group)
        user.save()

        # log verification
        # verified by email
        if entered_otp == otp_obj.email_otp:

            otp_obj.email_verified = True

            # invalidate whatsapp otp
            otp_obj.whatsapp_otp = None
            otp_obj.whatsapp_verified = False

            otp_obj.verified_via = "email"
            
        # verified by whatsapp
        elif entered_otp == otp_obj.whatsapp_otp:

            otp_obj.whatsapp_verified = True

            # invalidate email otp
            otp_obj.email_otp = None
            otp_obj.email_verified = False

            otp_obj.verified_via = "whatsapp"
        otp_obj.verified_at = timezone.now()
        otp_obj.is_completed = True

        # invalidate email otp too after use
        otp_obj.email_otp = None

        otp_obj.save()
        resume = Resume.objects.get(
                user=user
            )

        phone = resume.phone

        phone = phone.replace("+", "")
        phone = phone.replace(" ", "")
        if not phone.startswith("91"):
            phone = "91" + phone

        threading.Thread(
            target=send_verified_whatsapp_message,
            args=(user, phone),
            daemon=True
        ).start()
        threading.Thread(
            target=send_welcome_email,
            args=(user,),
            daemon=True
        ).start()
        login(
            request,
            user,
            backend='django.contrib.auth.backends.ModelBackend'    
        )
        messages.success(
            request,
            "Account verified successfully."
        )
        return redirect('dashboard')
    return render(request, "otp.html")


@never_cache
def resend_otp(request):

    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    otp = str(random.randint(100000, 999999))

    otp_obj, created = OTPVerification.objects.get_or_create(
        user=user
    )

    otp_obj.email_otp = otp
    otp_obj.email_verified = False
    otp_obj.email_attempts = 0
    otp_obj.expires_at = timezone.now() + timedelta(minutes=10)

    # invalidate whatsapp otp
    otp_obj.whatsapp_otp = None
    otp_obj.whatsapp_verified = False

    otp_obj.save()

    threading.Thread(
        target=send_otp_email,
        args=(otp, user),
        daemon=True
    ).start()

    messages.success(
        request,
        "New OTP sent to your email."
    )

    return redirect('verify_otp')


# -------------------------
# LOGIN
# -------------------------
@never_cache
def user_login(request):
    # Already logged in
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = UserLoginForm(request.POST or None)

    if request.method == "POST":

        # -----------------------------
        # FORM VALIDATION
        # -----------------------------
        if not form.is_valid():
            return render(
                request,
                "auth/user_login.html",
                {
                    "form": form,
                },
            )

        # -----------------------------
        # GET CLEANED CREDENTIALS
        # -----------------------------
        email = form.cleaned_data["email"].strip()
        password = form.cleaned_data["password"]

        # UserLoginForm has already resolved the email to the account whose
        # password matches. Do not call User.objects.get(email=...) here: a
        # legacy database can contain duplicate email addresses.
        existing_user = form.get_user()

        if existing_user is None:
            messages.error(request, "Unable to find the account for this login.")
            return render(request, "auth/user_login.html", {"form": form})

        # -----------------------------
        # CHECK OTP VERIFICATION
        # -----------------------------
        if not existing_user.is_active:
            request.session["user_id"] = existing_user.id

            messages.warning(
                request,
                "Your account is not verified. Please verify your OTP first."
            )

            return redirect("verify_otp")
        
        if existing_user.is_superuser:
            messages.warning(
                request,
                "This is not a valid account."
            )
            return redirect("user_login")
            
        # -----------------------------
        # AUTHENTICATE USER
        # -----------------------------
        user = authenticate(
            request,
            username=existing_user.username,
            password=password,
        )

        # -----------------------------
        # INVALID PASSWORD
        # -----------------------------
        if user is None:
            messages.error(
                request,
                "Invalid email or password."
            )

            return render(
                request,
                "auth/user_login.html",
                {
                    "form": form,
                },
            )

        # -----------------------------
        # FINAL ACTIVE CHECK
        # -----------------------------
        if not user.is_active:
            request.session["user_id"] = user.id

            messages.warning(
                request,
                "Please verify your OTP first."
            )

            return redirect("verify_otp")

        # -----------------------------
        # LOGIN
        # -----------------------------
        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        messages.success(
            request,
            f"Welcome {user.username}"
        )

        return redirect("dashboard")

    # GET request
    return render(
        request,
        "auth/user_login.html",
        {
            "form": form,
        },
    )


# -------------------------
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    resume = Resume.objects.get(user=request.user)
    sessions = get_user_sessions(
        request.user,
        request.session.session_key   # ✅ mark current device
    )
    # ✅ dynamic subdomain URL
    host = request.get_host()
    url = f"{request.scheme}://{resume.subdomain}.{host}"
    return render(request, "dashboard.html", {
        "resume": resume,
        "sessions": sessions,
        "url": url
    })


# -------------------------
# EDIT RESUME
# -------------------------
@login_required
def edit_resume(request):
    resume = Resume.objects.get(user=request.user)

    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)

        if form.is_valid():
            if 'subdomain' in form.changed_data:
                messages.warning(request, "Subdomain changed. Old URL will stop working.")

            form.save()
            return redirect('dashboard')
    else:
        form = ResumeForm(instance=resume)

    return render(request, "edit_resume.html", {"form": form})


# -------------------------
# PUBLIC RESUME VIEW
# -------------------------
def resume_view(request):
    resume = get_resume(request)

    if not resume:
        return render(request, "themes/no_resume.html")

    template_name = f"themes/{resume.theme}/index.html"
    fallback = "themes/default/index.html"

    try:
        return render(request, template_name, {"resume": resume})
    except TemplateDoesNotExist:
        return render(request, fallback, {"resume": resume})


# -------------------------
# CONTACT FORM
# -------------------------
def submit_contact_form(request):
    if request.method == 'POST':
        resume = get_resume(request)

        section = ContactSection.objects.filter(
            resume=resume,
            is_active=True
        ).first()

        form = ContactForm(request.POST)

        if form.is_valid() and section:
            contact = form.save(commit=False)
            contact.section = section
            contact.save()

            send_mail(
                subject=f"Contact Form: {contact.subject}",
                message=f"""
                Name: {contact.name}
                Email: {contact.email}

                Message:
                {contact.message}
                """,
                from_email=None,
                recipient_list=[section.receive_email_at],
                fail_silently=False,
            )

            messages.success(request, "Message sent successfully.")
            return redirect('/')

    return redirect('/')


# -------------------------
# DOWNLOAD PDF
# -------------------------
def download_resume_pdf(request):
    resume = get_resume(request)

    buffer = generate_resume_pdf(resume, request)
    return FileResponse(buffer, as_attachment=True, filename="resume.pdf")


# -------------------------
# DOWNLOAD DOCX
# -------------------------
def download_resume_docx(request):
    resume = get_resume(request)

    buffer = generate_resume_docx(resume)
    return FileResponse(buffer, as_attachment=True, filename="resume.docx")


# -------------------------
# ADMIN PDF PREVIEW
# -------------------------
def preview_resume_pdf(request, pk):
    resume = Resume.objects.get(id=pk)
    buffer = generate_resume_pdf(resume, request)

    return HttpResponse(buffer.getvalue(), content_type='application/pdf')


# -------------------------
# LOGOUT ALL DEVICES
# -------------------------
@login_required
def logout_all_devices(request):
    # delete all sessions
    delete_user_sessions(request.user)

    # logout current user
    logout(request)

    messages.success(
        request,
        "Logged out from all devices successfully."
    )
    return redirect('user_login')


def password_change_cleanup(request):
    delete_user_sessions(
        request.user,
        keep_current_session_key=request.session.session_key
    )

   
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'auth/change_password.html'   # your template
    success_url = '/change-password/done/'
    
    def form_valid(self, form):
        response = super().form_valid(form)

        # ✅ logout all other devices
        delete_user_sessions(
            self.request.user,
            keep_current_session_key=self.request.session.session_key
        )

        return response


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)

        # 🔥 logout all devices after password reset
        user = form.user
        delete_user_sessions(user)

        return response

 
def csrf_failure(request, reason=""):
    # CSRF failures are not necessarily OTP/session failures. In particular,
    # the Django admin login must be allowed to return to its own login page.
    messages.error(
        request,
        "Your session expired or the security token was invalid. Please try again."
    )

    if request.path.startswith("/admin/"):
        return redirect("/admin/login/")

    return redirect("user_login")


@csrf_protect
def verify_whatsapp_otp(request):

    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('register')

    user = User.objects.get(id=user_id)

    otp_obj = OTPVerification.objects.get(user=user)

    if request.method == "POST":

        otp = request.POST.get('otp')

        # check expiry
        if timezone.now() > otp_obj.expires_at:

            messages.error(
                request,
                "OTP expired. Please resend."
            )

            return redirect('resend_whatsapp_otp')

        # invalid otp
        if otp != otp_obj.whatsapp_otp:

            otp_obj.whatsapp_attempts += 1
            otp_obj.save()

            messages.error(
                request,
                "Invalid OTP"
            )

            return redirect('verify_whatsapp_otp')

        # success
        user.is_active = True
        user.save()

        otp_obj.whatsapp_verified = True

        otp_obj.email_otp = None
        otp_obj.email_verified = False

        otp_obj.whatsapp_otp = None

        otp_obj.verified_via = "whatsapp"

        otp_obj.verified_at = timezone.now()

        otp_obj.is_completed = True

        otp_obj.save()
        resume = Resume.objects.get(
            user=user
        )

        phone = resume.phone

        phone = phone.replace("+", "")
        phone = phone.replace(" ", "")

        if not phone.startswith("91"):
            phone = "91" + phone

        threading.Thread(
            target=send_verified_whatsapp_message,
            args=(user, phone),
            daemon=True
        ).start()
        login(
            request,
            user,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        messages.success(
            request,
            "WhatsApp verified successfully"
        )

        return redirect('dashboard')

    return render(
        request,
        "auth/otp/verify_whatsapp_otp.html"
    )


# -------------------------
# RESEND WHATSAPP OTP
# -------------------------
@never_cache
def resend_whatsapp_otp(request):

    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)

    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    try:
        resume = Resume.objects.get(user=user)

    except Resume.DoesNotExist:
        messages.error(request, "Resume not found for this account.")
        return redirect('register')

    otp = str(random.randint(100000, 999999))

    otp_obj, created = OTPVerification.objects.get_or_create(
        user=user
    )

    otp_obj.whatsapp_otp = otp
    otp_obj.whatsapp_verified = False
    otp_obj.whatsapp_attempts = 0
    otp_obj.expires_at = timezone.now() + timedelta(minutes=10)

    otp_obj.save()

    phone = str(resume.phone)
    phone = phone.replace("+", "")
    phone = phone.replace(" ", "")

    if not phone.startswith("91"):
        phone = "91" + phone

    otp_message = get_whatsapp_message(
        "otp",
        {
            "username": user.username,
            "otp": otp,
            "email": user.email,
        }
    )

    if otp_message:
        threading.Thread(
            target=WhatsAppService.send,
            args=(phone, otp_message),
            daemon=True
        ).start()

    messages.success(
        request,
        "New OTP sent to your WhatsApp."
    )

    return redirect('verify_whatsapp_otp')


def test_whatsapp(request):
    
    otp = generate_otp()

    WhatsAppService.send(
        "+919876543210",
        f"Your OTP is {otp}"
    )

    return HttpResponse("WhatsApp Sent")