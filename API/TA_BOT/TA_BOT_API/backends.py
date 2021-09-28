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
            user = user_model.objects.get(email=username)
            print(user)
            if user.check_password(password):
                chat_id = request.data.get('chat_id')
                if chat_id is None:
                    raise ValidationError('Chat_id is not sent in response body!')
                sessions = [session.chat_id for session in user.active_sessions.all()]
                if chat_id not in sessions:
                    new_session = TelegramActiveSessions(chat_id=chat_id, user=user)
                    new_session.save()
                    user.active_sessions.add(new_session)
                    user.save()
                print(user)
                return user
        except user_model.DoesNotExist:
            print('here')
            return None

    def get_user(self, user_id):
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None