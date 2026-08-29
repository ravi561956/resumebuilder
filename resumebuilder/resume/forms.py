from django import forms
from django.core.exceptions import ValidationError
from .models import Resume
from .models import Profession, ResumeStat
from .models import ContactMessage
from django.contrib.auth.models import User
from apps.moderation.services import validate_resume_content
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class UserLoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email",
            "autocomplete": "email",
        }),
    )

    password = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password",
            "autocomplete": "current-password",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email or not password:
            return cleaned_data

        # Do not use User.objects.get(email=...) here. Existing databases may
        # contain duplicate email addresses (for example, accounts created
        # before email uniqueness was enforced). Find the account whose
        # password actually matches instead.
        matching_users = list(
            User.objects.filter(email__iexact=email, is_active=True)
        )

        if not matching_users:
            # Also check inactive accounts so the user gets the OTP/activation
            # message from the login view rather than a generic error.
            matching_users = list(User.objects.filter(email__iexact=email))

        if not matching_users:
            raise forms.ValidationError(
                "No account exists with this email address."
            )

        password_users = [
            candidate for candidate in matching_users
            if candidate.check_password(password)
        ]

        if not password_users:
            raise forms.ValidationError(
                "Incorrect password. Please try again."
            )

        # If legacy duplicate accounts exist, only accept the login when the
        # password identifies exactly one account. This avoids arbitrarily
        # logging into the wrong account.
        if len(password_users) > 1:
            raise forms.ValidationError(
                "Multiple accounts use this email and password. Please contact support."
            )

        user = password_users[0]
        self.user_cache = user

        if not user.is_active:
            return cleaned_data

        # Authenticate through Django's configured backend and keep the
        # explicit ModelBackend selection because multiple backends are
        # configured for social login.
        self.user_cache = authenticate(
            request=None,
            username=user.get_username(),
            password=password,
        )

        if self.user_cache is None:
            raise forms.ValidationError(
                "Unable to authenticate your account."
            )

        return cleaned_data

    def get_user(self):
        return getattr(self, "user_cache", None)
    
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    subdomain = forms.CharField()
    phone = forms.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        
    def clean_username(self):
    
        username = self.cleaned_data['username']

        if User.objects.filter(
            username=username
        ).exists():

            raise forms.ValidationError(
                "Username already exists."
            )

        return username

    def clean_email(self):

        email = self.cleaned_data['email']

        if User.objects.filter(
            email=email
        ).exists():

            raise forms.ValidationError(
                "Email already exists."
            )

        if Resume.objects.filter(
            email=email
        ).exists():

            raise forms.ValidationError(
                "Resume email already exists."
            )

        return email

    def clean_phone(self):

        phone = self.cleaned_data['phone']

        phone = (
            phone.replace("+", "")
            .replace(" ", "")
        )

        if Resume.objects.filter(
            phone=phone
        ).exists():

            raise forms.ValidationError(
                "Phone number already exists."
            )

        return phone

    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain'].lower()

        if Resume.objects.filter(
            subdomain=subdomain
        ).exists():

            raise forms.ValidationError(
                "Subdomain already taken."
            )

        return subdomain   
        
        
class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = '__all__'
        
    def clean(self):
    
        cleaned_data = super().clean()

        instance = self.instance

        for field_name, value in cleaned_data.items():

            if hasattr(instance, field_name):
                setattr(instance, field_name, value)

        # try:
        #     validate_resume_content(instance)

        # except ValidationError as e:

        #     raise forms.ValidationError(
        #         e.messages[0]
        #     )

        return cleaned_data

class ProfessionForm(forms.ModelForm):
    class Meta:
        model = Profession
        fields = '__all__'
        widgets = {
            'resume_stats': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['resume_stats'].queryset = ResumeStat.objects.filter(
                resume=self.instance.resume
            )


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')