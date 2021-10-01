from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.views.generic.base import View
import requests

from rest_framework import status
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import APIException, NotFound, ValidationError
from telegram import chat

from .serializers import UserRegisterSerializer, AccountActivitionSerializer,AdminRegisterSerializer, LogoutSerializer, CategorySerilizer
from .models import AuthData, Category
from .exceptions import UserAlreadyExistsException,NoOtpException,InvalidSecretKey, OtpMismatchException

from smtplib import SMTPException
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

import redis

user_model = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,port=settings.REDIS_PORT, db=0)
secret = getattr(settings, 'SECRET_KEY', 'thikiuridi')

class LoginApiView(ObtainAuthToken):
    ''' A view for login users.\n
        /api/auth/login (POST)
    '''

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class AuthView(ViewSet):

    authentication_classes = [TokenAuthentication]
    
    def register_user(self, request):
        seri = UserRegisterSerializer(data=request.data)
        if seri.is_valid():
            email = seri.validated_data.get('email')

            # Checking if the email already exsits in redis keys
            otp = redis_instance.get(email.lower())

            if otp is None:
                # Checking if the user has registered before
                try:
                    user = user_model.objects.get(email__iexact=email)
                    # Checking if user has activated his/her account already
                    if user.is_active:
                        raise UserAlreadyExistsException('A user with this email already exists!')
                except user_model.DoesNotExist:
                    # Create a new user if user does not exist
                    try:
                        auth_data = AuthData.objects.get(email__iexact=email)
                        print(auth_data.student_id)
                        user_model.objects.create_user(email, auth_data.first_name, auth_data.last_name, auth_data.student_id, student_id=auth_data.student_id)
                    except AuthData.DoesNotExist:
                        raise NotFound(detail='Student not found in database.')
            
            # Create OTP and save in redis
            otp = get_random_string(length=5, allowed_chars='0123456789')
            redis_instance.set(name=email.lower(), value=otp, ex= 60 * 5)
            
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
                raise APIException('Can not send the email.')
            return Response(data={}, status=status.HTTP_200_OK)
        raise ValidationError(detail='The data is not valid!')

    def activate_account(self, request):
        seri = AccountActivitionSerializer(data=request.data)
        if seri.is_valid():
            # Getting request data
            email = seri.validated_data.get('email')
            given_otp = seri.validated_data.get('otp')

            # Checking if the otp is correct
            otp = redis_instance.get(email)
            if otp is None:
                raise NoOtpException(detail='You have not requested an otp yet.')

            if given_otp != otp.decode('utf-8'):
                raise OtpMismatchException('Otp is not correct!')

            # Activate account
            user = user_model.objects.get(email__iexact=email)
            user.is_active = True
            user.save()

            # Delete from reddit
            redis_instance.delete(email)
            
            return Response(data={}, status=status.HTTP_200_OK)

        raise ValidationError(detail='The data is not valid!')

    def register_admin(self, request):
        seri = AdminRegisterSerializer(data=request.data)
        if seri.is_valid():
            email = seri.validated_data.get('email')
            given_secret = seri.validated_data.get('secret')

            if given_secret != secret:
                raise InvalidSecretKey(detail='The entered secret key is incorrect.')
            
            try:
                user_model.objects.get(email__iexact=email)
                raise UserAlreadyExistsException(detail='A user with this email already exists!')
            except user_model.DoesNotExist:
                user_model.objects.create_superuser(email, secret)

            return Response(data={}, status=status.HTTP_200_OK) 
        
        raise ValidationError(detail='The data is not valid!')

    def logout(self, request):
        seri = LogoutSerializer(data=request.data)
        if seri.is_valid():
            chat_id = seri.validated_data.get('chat_id')
            
            # Delete chat_id from user sessions
            user = request.user
            user.active_sessions.filter(chat_id=chat_id).delete()

            return Response(data={}, status=status.HTTP_200_OK) 
        
        raise ValidationError(detail='The data is not valid!')

class MemberCategoryView(ViewSet):

    authentication_classes = [TokenAuthentication]

    def get_all_categories(self,request):
        categories = Category.objects.all()
        seri = CategorySerilizer(categories, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)