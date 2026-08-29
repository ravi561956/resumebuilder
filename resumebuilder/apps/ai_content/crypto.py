"""Small helper for encrypting payment secrets at rest.

The encryption key is derived from Django SECRET_KEY. Changing SECRET_KEY makes
previously encrypted values unreadable, so SECRET_KEY must be kept stable when
payment gateway settings are stored in the database.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


_PREFIX = 'enc$'


def _fernet():
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(value):
    if value in (None, ''):
        return value or ''
    value = str(value)
    if value.startswith(_PREFIX):
        return value
    return _PREFIX + _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def decrypt(value):
    if value in (None, ''):
        return value or ''
    value = str(value)
    if not value.startswith(_PREFIX):
        # Backward compatibility for installations that already stored the
        # credentials before encrypted-at-rest support was added.
        return value
    try:
        return _fernet().decrypt(value[len(_PREFIX):].encode('ascii')).decode('utf-8')
    except InvalidToken as exc:
        raise ValueError('Unable to decrypt payment credentials. Check that DJANGO_SECRET_KEY has not changed.') from exc
