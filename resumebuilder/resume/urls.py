from django.urls import path
from .views import *
from .views import preview_resume_pdf
from .views import logout_all_devices
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetConfirmView

urlpatterns = [
    path('', landing, name='landing'),   # MAIN DOMAIN
    path('login/', user_login, name='user_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('resume/', resume_view, name='resume'),  # OPTIONAL
    path('register/', register, name='register'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('dashboard/', dashboard, name='dashboard'),
    # path('edit/', edit_resume),
    path('contact/submit/', submit_contact_form, name='contact_submit'),
    path('logout-all/', logout_all_devices, name='logout_all_devices'),
    path('resume/pdf/', download_resume_pdf, name='resume_pdf'),
    path('resume/doc/', download_resume_docx, name='resume_doc'),
    path('resume:preview-pdf/<int:pk>/', preview_resume_pdf, name='resume_pdf_preview'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/change_password_done.html'
    ), name='password_change_done'),
    path('reset-password/', auth_views.PasswordResetView.as_view(
        template_name='auth/reset_password.html',
        html_email_template_name='auth/reset_password_email.html',
        email_template_name='auth/reset_password_email.txt',
        subject_template_name='auth/reset_password_subject.txt'
    ), name='password_reset'),
    path('reset-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/reset_password_done.html'
    ), name='password_reset_done'),
    path('reset-password-confirm/<uidb64>/<token>/',
         CustomPasswordResetConfirmView.as_view(
             template_name='auth/reset_password_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset-password-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/reset_password_complete.html'
         ),
         name='password_reset_complete'),
    path('test-whatsapp/',test_whatsapp,name='test_whatsapp'),
    path(
        'verify-whatsapp-otp/',
        verify_whatsapp_otp,
        name='verify_whatsapp_otp'
    ),
]