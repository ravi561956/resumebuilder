from django import forms
from .models import Resume
from django import forms
from .models import Profession, ResumeStat
from .models import ContactMessage
from django.contrib.auth.models import User


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