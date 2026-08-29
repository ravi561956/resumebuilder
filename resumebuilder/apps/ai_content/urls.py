from django.urls import path
from . import views

app_name = 'ai_content'

urlpatterns = [
    path('', views.ai_dashboard, name='dashboard'),
    path('packages/<int:package_id>/order/', views.create_order, name='create_order'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path('payment/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('generate/resume/', views.generate_resume_content, name='generate_resume_content'),
    path('generate/component/', views.generate_component_content, name='generate_component_content'),
    path('cover-letter/', views.cover_letter, name='cover_letter'),
]
