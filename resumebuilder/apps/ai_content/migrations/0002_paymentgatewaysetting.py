from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_content', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentGatewaySetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False)),
                ('gateway', models.CharField(choices=[('razorpay', 'Razorpay')], default='razorpay', max_length=30)),
                ('mode', models.CharField(choices=[('test', 'Test / Sandbox'), ('live', 'Live / Production')], default='test', max_length=10)),
                ('key_id', models.CharField(blank=True, max_length=255)),
                ('key_secret', models.CharField(blank=True, max_length=255)),
                ('webhook_secret', models.CharField(blank=True, max_length=255)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('checkout_name', models.CharField(default='Resume Builder', max_length=100)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Payment Gateway Setting',
                'verbose_name_plural': 'Payment Gateway Setting',
            },
        ),
    ]
