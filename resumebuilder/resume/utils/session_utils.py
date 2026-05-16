from django.contrib.sessions.models import Session
from django.utils import timezone


def get_user_sessions(user, current_session_key=None):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_sessions = []

    for session in sessions:
        data = session.get_decoded()

        if data.get('_auth_user_id') == str(user.id):
            user_sessions.append({
                'session_key': session.session_key,
                'expire_date': session.expire_date,
                'is_current': session.session_key == current_session_key
            })

    return user_sessions


def delete_user_sessions(user, keep_current_session_key=None):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in sessions:
        data = session.get_decoded()

        if data.get('_auth_user_id') == str(user.id):
            if keep_current_session_key and session.session_key == keep_current_session_key:
                continue
            session.delete()