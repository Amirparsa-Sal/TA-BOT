from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings

from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.exceptions import APIException, NotFound, ValidationError

from .serializers import UserRegisterSerializer, AccountActivitionSerializer
from .models import AuthData
from .exceptions import UserAlreadyExistsException,NoOtpException

from smtplib import SMTPException

import redis

user_model = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,port=settings.REDIS_PORT, db=0)

class AuthView(ViewSet):

    def register_user(self, request):
        seri = UserRegisterSerializer(data=request.data)
        if seri.is_valid():
            email, chat_id = seri.validated_data.get('email'), seri.validated_data.get('chat_id')

            # Checking if the user has registered before
            user = None
            try:
                user = user_model.objects.get(email=email)
                # Checking if user has activated his/her account already
                if user.is_active:
                    raise UserAlreadyExistsException('A user with this email already exists!')
            except:
                # Finding the user student id and save the user it in database
                try:
                    auth_data = AuthData.objects.get(email=email)
                    user = user_model.objects.create_user(email, chat_id, auth_data.first_name, auth_data.last_name, auth_data.student_id)
                except AuthData.DoesNotExist:
                    raise NotFound(detail='Student not found in database.')
            finally:
                # Create OTP and save in redis
                otp = get_random_string(length=5, allowed_chars='0123456789')
                redis_instance.set(name=chat_id, value=otp)
                
                # Send OTP via email
                try:    
                    send_mail(
                        'C Fall 2021 Bot Registeration',
                        f'your confirmation code is: {otp}',
                        'from@example.com',
                        [email],
                        fail_silently=False,
                    )
                except SMTPException as e:
                    print(e)
                    raise APIException('Can not send the email.')
            return Response(data={}, status=status.HTTP_200_OK)
        raise ValidationError(detail='The data is not valid!')

    def activate_account(self, request):
        seri = AccountActivitionSerializer(data=request.data)
        if seri.is_valid():
            # Getting request data
            chat_id = seri.validated_data.get('chat_id')
            given_otp = seri.validated_data.get('otp')
            
            # Checking if the otp is correct
            otp = redis_instance.get(chat_id)
            if otp is None:
                raise NoOtpException(detail='You have not requested an otp yet.')

            try:
                # Activate account of the otp is correct
                user = user_model.objects.get(chat_id=chat_id)
                user.is_active = True
                user.save()
                return Response(data={}, status=status.HTTP_200_OK)
            except:
                raise NotFound(detail='User not found in database with this chat_id!')

        raise ValidationError(detail='The data is not valid!')
