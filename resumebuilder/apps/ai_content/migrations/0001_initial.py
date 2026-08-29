from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('resume', '0039_remove_resume_moderated_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('tokens', models.PositiveIntegerField(help_text='AI credit/token balance added to the user after successful payment.')),
                ('price', models.DecimalField(decimal_places=2, help_text='Price in INR.', max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('display_order', 'price', 'id')},
        ),
        migrations.CreateModel(
            name='AIContentSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ai_content_enabled', models.BooleanField(default=True)),
                ('paid_ai_required', models.BooleanField(default=True)),
                ('default_generation_cost', models.PositiveIntegerField(default=500, help_text='Default credits charged for one AI content request when the exact API token usage is unavailable.')),
                ('max_output_tokens', models.PositiveIntegerField(default=800)),
                ('system_prompt', models.TextField(blank=True, default='You are a professional resume and career-writing assistant. Write truthful, concise, ATS-friendly professional content. Never invent employers, qualifications, dates, metrics or achievements. Return only the requested content.')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'AI Content Setting', 'verbose_name_plural': 'AI Content Setting'},
        ),
        migrations.CreateModel(
            name='CoverLetterSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True)),
                ('free_for_users', models.BooleanField(default=True, help_text='When enabled, normal users can generate cover letters without consuming purchased AI credits.')),
                ('max_output_tokens', models.PositiveIntegerField(default=1000)),
                ('prompt_template', models.TextField(blank=True, default='Create a tailored professional cover letter using the candidate resume and the supplied job description. Do not invent facts. Keep it concise and suitable for a job application.')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Cover Letter Setting', 'verbose_name_plural': 'Cover Letter Setting'},
        ),
        migrations.CreateModel(
            name='AICreditBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchased_tokens', models.PositiveBigIntegerField(default=0)),
                ('used_tokens', models.PositiveBigIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_credit_balance', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AIPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('tokens', models.PositiveIntegerField()),
                ('gateway', models.CharField(default='razorpay', max_length=30)),
                ('gateway_order_id', models.CharField(blank=True, db_index=True, max_length=150)),
                ('gateway_payment_id', models.CharField(blank=True, db_index=True, max_length=150)),
                ('gateway_signature', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('created', 'Created'), ('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='created', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='ai_content.aipackage')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='AICreditTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('purchase', 'Purchase'), ('generation', 'Generation'), ('refund', 'Refund'), ('adjustment', 'Admin Adjustment')], max_length=20)),
                ('tokens', models.IntegerField(help_text='Positive adds credits; negative consumes credits.')),
                ('description', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('purchase', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='ai_content.aipurchase')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_credit_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='AIGeneration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature', models.CharField(choices=[('resume_content', 'Resume Content'), ('cover_letter', 'Cover Letter')], max_length=30)),
                ('field_name', models.CharField(blank=True, max_length=100)),
                ('prompt', models.TextField()),
                ('output', models.TextField(blank=True)),
                ('input_tokens', models.PositiveIntegerField(default=0)),
                ('output_tokens', models.PositiveIntegerField(default=0)),
                ('total_tokens', models.PositiveIntegerField(default=0)),
                ('charged_tokens', models.PositiveIntegerField(default=0)),
                ('is_free', models.BooleanField(default=False)),
                ('status', models.CharField(default='success', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resume', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_generations', to='resume.resume')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_generations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-created_at',)},
        ),

        migrations.RunPython(
            lambda apps, schema_editor: (
                apps.get_model('ai_content', 'AIContentSetting').objects.get_or_create(pk=1),
                apps.get_model('ai_content', 'CoverLetterSetting').objects.get_or_create(pk=1),
            ),
            migrations.RunPython.noop,
        ),
    ]
