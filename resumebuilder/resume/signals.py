from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models.signals import pre_save
from .utils.session_utils import delete_user_sessions

@receiver(post_delete, sender=User)
def delete_user_sessions_on_delete(sender, instance, **kwargs):
    """
    When a user is deleted, remove all active sessions of that user.
    """

    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in sessions:
        data = session.get_decoded()

        # '_auth_user_id' is stored as string
        if data.get('_auth_user_id') == str(instance.id):
            session.delete()
            
@receiver(pre_save, sender=User)
def logout_user_if_deactivated(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old_user.is_active and not instance.is_active:
        # user is being deactivated → kill sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())

        for session in sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(instance.id):
                session.delete()
                
@receiver(pre_save, sender=User)
def logout_on_password_change(sender, instance, **kwargs):

    if not instance.pk:
        return

    try:
        old_user = User.objects.get(pk=instance.pk)

    except User.DoesNotExist:
        return

    # password changed
    if old_user.password != instance.password:

        sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )

        for session in sessions:

            data = session.get_decoded()

            if data.get('_auth_user_id') == str(instance.id):

                session.delete()