from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.ai_content.models import AIPackage, AIContentSetting, CoverLetterSetting


class Command(BaseCommand):
    help = 'Create safe local-development AI settings and a test credit package.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_ai_dev is disabled when DEBUG=False.')

        ai_setting = AIContentSetting.get()
        ai_setting.ai_content_enabled = True
        ai_setting.paid_ai_required = True
        ai_setting.save(update_fields=['ai_content_enabled', 'paid_ai_required', 'updated_at'])

        cover_setting = CoverLetterSetting.get()
        cover_setting.enabled = True
        cover_setting.free_for_users = True
        cover_setting.save(update_fields=['enabled', 'free_for_users', 'updated_at'])

        package, created = AIPackage.objects.get_or_create(
            name='Developer Test Package',
            defaults={
                'description': 'Local development package. No Razorpay payment is required when DEBUG=True.',
                'tokens': 10000,
                'price': 1,
                'is_active': True,
                'display_order': 0,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'AI development setup ready. Package={package.name}, tokens={package.tokens}, price=₹{package.price}. '
            f'Created={created}.'
        ))
