import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework.exceptions import ValidationError
from .models import TelegramActiveSessions

user_model = get_user_model()

class AuthenticationBackend(ModelBackend):
    """
    Custom Email Backend to handle active sessions.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = user_model.objects.get(email__iexact=username)
            if user.check_password(password):
                # if user is superuser its ok
                if user.is_superuser:
                    return user
                # if not, get chat id to add session
                chat_id = request.data.get('chat_id', None)
                if chat_id is None:
                    raise ValidationError('Chat_id is not sent in response body!')
                chat_id = int(chat_id)
                # remove chat_id from other users session
                TelegramActiveSessions.objects.filter(chat_id=chat_id).delete()
                # if user is staff its ok
                if user.is_staff:
                    return user
                # add chat_id to user sessions if not exists
                sessions = [session.chat_id for session in user.active_sessions.all()]
                if chat_id not in sessions:
                    new_session = TelegramActiveSessions(chat_id=chat_id, user=user)
                    new_session.save()
                    user.active_sessions.add(new_session)
                    user.save()
                return user
        except user_model.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None