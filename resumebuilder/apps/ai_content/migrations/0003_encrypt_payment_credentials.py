from django.db import migrations, models


def encrypt_existing(apps, schema_editor):
    from apps.ai_content.crypto import encrypt
    Model = apps.get_model('ai_content', 'PaymentGatewaySetting')
    for obj in Model.objects.all().iterator():
        changed = False
        for field in ('key_id', 'key_secret', 'webhook_secret'):
            value = getattr(obj, field) or ''
            if value and not value.startswith('enc$'):
                setattr(obj, field, encrypt(value))
                changed = True
        if changed:
            obj.save(update_fields=['key_id', 'key_secret', 'webhook_secret'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [('ai_content', '0002_paymentgatewaysetting')]

    operations = [
        migrations.AlterField('paymentgatewaysetting', 'key_id', models.CharField(blank=True, max_length=1000)),
        migrations.AlterField('paymentgatewaysetting', 'key_secret', models.CharField(blank=True, max_length=1000)),
        migrations.AlterField('paymentgatewaysetting', 'webhook_secret', models.CharField(blank=True, max_length=1000)),
        migrations.RunPython(encrypt_existing, noop),
    ]
