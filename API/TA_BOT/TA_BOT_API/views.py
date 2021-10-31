from os import stat
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.checks import messages
from django.core.mail import send_mail
from django.db.models.query_utils import Q
from django.utils.crypto import get_random_string
from django.conf import settings
from django.views.generic.base import View
from django.db.models import Q

from rest_framework import serializers, status
from rest_framework import permissions
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.authtoken.models import Token


from .serializers import AnswerSerializer, ChatIdMessageIdSerializer, GradeSerializer, QuestionAnswerSerializer, QuestionSerializer, ResourcePartialUpdateSerializer, UserRegisterSerializer, AccountActivitionSerializer,AdminRegisterSerializer, \
    ChatIdSerializer, CategorySerilizer, ResourceSerializer, HomeWorkSerializer, HomeWorkPartialUpdateSerializer \

from .models import AuthData, Category, Grade, QuestionAnswer, TelegramActiveSessions, Resource, HomeWork
from .exceptions import UserAlreadyExistsException,NoOtpException,InvalidSecretKey, OtpMismatchException

from smtplib import SMTPException
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from django.db import transaction

import redis

user_model = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,port=settings.REDIS_PORT, db=0)
secret = getattr(settings, 'SECRET_KEY', 'thikiuridi')

from rest_framework.authtoken.models import Token

class BotMetaDataView(ViewSet):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_last_login(self, request):
        chat_id = request.GET.get('chat_id', None)
        if chat_id is None:
            raise ValidationError(detail='chat_id is not in request params!')

        # Delete chat_id from user sessions
        try:
            active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
            token = Token.objects.get(user=active_session.user)
            return Response(data={'token': token.key, 'is_admin':active_session.user.is_staff}, status=status.HTTP_200_OK) 
        except TelegramActiveSessions.DoesNotExist:
            return Response(data={'token': None}, status=status.HTTP_200_OK)

    def get_all_active_sessions(self, request):
        user_id = request.GET.get('user_id', None)
        if user_id is None:
            raise ValidationError(detail='user_id is not in request params!')

        # Find all active sessions
        active_sessions = TelegramActiveSessions.objects.filter(user__id=user_id)
        chat_id_list = [session.chat_id for session in active_sessions]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)
    
    def get_all_students_sessions(self, request):
        active_sessions = TelegramActiveSessions.objects.filter(user__is_staff=False)
        chat_id_list = [session.chat_id for session in active_sessions]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)

    
class CustomAuthToken(ObtainAuthToken):
    ''' A view for login users.\n
        /api/auth/login (POST)
    '''

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                       context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'is_admin': user.is_staff
        })

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
        seri = ChatIdSerializer(data=request.data)
        if seri.is_valid():
            chat_id = seri.validated_data.get('chat_id')
            
            # Delete chat_id from user sessions
            user = request.user
            user.active_sessions.filter(chat_id=chat_id).delete()

            return Response(data={}, status=status.HTTP_200_OK) 
        
        raise ValidationError(detail='The data is not valid!')
        

class MemberCategoryView(ViewSet):

    authentication_classes = [TokenAuthentication]
    serializer_class = CategorySerilizer
    resource_serializer_class = ResourceSerializer
    question_serializer_class = QuestionSerializer
    question_answer_serializer_class =QuestionAnswerSerializer
    

    def get_all_categories(self, request):
        categories = Category.objects.all()
        seri = self.serializer_class(categories, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def get_resources(self, request, cat_id):
        try:
            category = Category.objects.get(pk=cat_id)
            resources = list(category.resources.all())
            seri = ResourceSerializer(resources, many=True)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

    @transaction.atomic
    def add_question(self, request, cat_id):
        seri = self.question_serializer_class(data=request.data)
        if seri.is_valid():
            try:
                category = Category.objects.get(pk=cat_id)
                question_answer = QuestionAnswer(question=seri.validated_data['question'], source_chat_id=seri.validated_data['chat_id'], user=request.user, category=category)
                question_answer.save()
                seri = self.question_answer_serializer_class(question_answer)
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except Category.DoesNotExist:
                raise NotFound(detail=f'Category(id = {cat_id}) not found!')
        raise ValidationError(detail=seri.errors)

class AdminCategoryView(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = CategorySerilizer

    def get_all_categories(self, request):
        categories = Category.objects.all()
        seri = self.serializer_class(categories, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def change_category_status(self, request, cat_id=None):
        try:
            category = Category.objects.get(pk=cat_id)
            category.is_taught = not category.is_taught
            category.save()
            seri = self.serializer_class(category)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

    def add_resource(self, request, cat_id):
        try:
            category = Category.objects.get(pk=cat_id)
            seri = ResourceSerializer(data=request.data)
            if seri.is_valid():
                resource = Resource(title=seri.validated_data.get('title'), \
                                    link=seri.validated_data.get('link'),
                                    category=category)
                resource.save()
                return Response(data=seri.data, status=status.HTTP_200_OK)
            raise ValidationError(detail='The data is not valid!')
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

    def get_all_resources(self, request, cat_id):
        try:
            category = Category.objects.get(pk=cat_id)
            resources = list(category.resources.all())
            seri = ResourceSerializer(resources, many=True)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

class AdminResourceView(ViewSet):

    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = ResourceSerializer

    def get_resource(self, request, res_id):
        try:
            res = Resource.objects.get(pk=res_id)
            seri = self.serializer_class(res)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Resource.DoesNotExist:
            raise NotFound(detail=f'Resource(id = {res_id}) not found!')

    def update_resource(self, request, res_id):
        try:
            res = Resource.objects.get(pk=res_id)
            seri = ResourcePartialUpdateSerializer(data=request.data)
            if seri.is_valid():
                res.title = seri.validated_data.get('title', res.title)
                res.link = seri.validated_data.get('link', res.link)
                res.save()
                return Response(data=seri.data, status=status.HTTP_200_OK)
            raise ValidationError(detail='The data is not valid!')
        except Resource.DoesNotExist:
            raise NotFound(detail=f'Resource(id = {res_id}) not found!')

    def delete_resource(self, request, res_id):
        try:
            res = Resource.objects.get(pk=res_id)
            res.delete()
            return Response(data=None, status=status.HTTP_200_OK)
        except Resource.DoesNotExist:
            raise NotFound(detail=f'Resource(id = {res_id}) not found!')

class AdminHomeWorkView(ViewSet):

    queryset = HomeWork.objects.all()
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = HomeWorkSerializer
    update_serializer_class = HomeWorkPartialUpdateSerializer
    grade_serializer_class = GradeSerializer

    def get_homework(self, request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            seri = self.serializer_class(hw)
            data = seri.data
            data['grade_link'] = hw.grade.link if hw.grade else None
            return Response(data=data, status=status.HTTP_200_OK)
        except:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')
    
    def get_all_homeworks(self, request):
        homeworks = HomeWork.objects.all()
        seri = self.serializer_class(homeworks, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def create_homework(self, request):
        seri = self.serializer_class(data=request.data)
        if seri.is_valid():
            hw = HomeWork(title=seri.validated_data.get('title'), \
                          file=seri.validated_data.get('file'), \
                          published=seri.validated_data.get('published'), \
                          due_date_time=seri.validated_data.get('due_date_time'))
            hw.save()
            seri = self.serializer_class(hw)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        raise ValidationError(detail='The data is not valid!')

    def delete_homework(self, request, hw_id=None):
        HomeWork.objects.filter(pk=hw_id).delete()
        return Response(data=None, status=status.HTTP_200_OK)

    def update_homework(self, request, hw_id=None):
        seri = self.update_serializer_class(data=request.data)
        if seri.is_valid():
            try:
                hw = HomeWork.objects.get(pk=hw_id)
                hw.title = seri.validated_data.get('title',hw.title)
                hw.file = seri.validated_data.get('file', hw.file)
                hw.due_date_time = seri.validated_data.get('due_date_time', hw.due_date_time)
                hw.published = seri.validated_data.get('published', hw.published)
                hw.save()
                seri = self.serializer_class(hw)
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except HomeWork.DoesNotExist:
                raise NotFound(detail=f'homework(id= {hw_id}) not found!')
        raise ValidationError(detail='The data is not valid!')

    def update_grade(self, request, hw_id=None):
        seri = self.grade_serializer_class(data=request.data)
        if seri.is_valid():
            try:
                hw = HomeWork.objects.get(pk=hw_id)
                grade = hw.grade
                if grade is not None:
                    grade.link = seri.validated_data.get('link')
                    grade.published = seri.validated_data.get('published')
                    grade.save()
                else:
                    grade = Grade(link=seri.validated_data.get('link'), published=seri.validated_data.get('published'))
                    grade.save()
                    hw.grade = grade
                    hw.save()
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except HomeWork.DoesNotExist:
                raise NotFound(detail=f'homework(id= {hw_id}) not found!')

        raise ValidationError(detail=seri.errors)

    def delete_grade(self ,request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            hw.grade = None
            hw.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def get_grade(self ,request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            grade = hw.grade
            if grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            seri = self.grade_serializer_class(grade)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def publish_grade(self, request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            if hw.grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            hw.grade.published = True
            hw.grade.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def unpublish_grade(self, request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            if hw.grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            hw.grade.published = False
            hw.grade.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

class MemberHomeworkView(ViewSet):

    authentication_classes = [TokenAuthentication]
    serializer_class = HomeWorkSerializer
    grade_serializer_class = GradeSerializer

    def get_published_homeworks(self, request):
        homeworks = HomeWork.objects.filter(published=True)
        seri = self.serializer_class(homeworks, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def get_homework(self, request, hw_id=None):
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            seri = self.serializer_class(hw)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def get_grade(self, request, hw_id):
        try:
            homework = HomeWork.objects.get(pk=hw_id)
            grade_serializer_class = GradeSerializer
            grade = homework.grade
            if grade is None or not grade.published:
                raise NotFound(detail=f'There is no grade for this hw!')
            seri = self.grade_serializer_class(grade)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'Homework(id = {hw_id}) not found!')

class AdminNotificationsView(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = ChatIdSerializer

    def get_incoming_notif_status(self, request):
        chat_id = int(request.GET.get('chat_id', None))
        if chat_id is not None:
            user = request.user
            try:
                active_session = TelegramActiveSessions.objects.get(user=user, chat_id=chat_id)
                return Response(data={'status': active_session.allow_notif}, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed!')

    def enable_notif(self, request):
        seri = self.serializer_class(data=request.data)
        if seri.is_valid():
            chat_id = int(seri.validated_data['chat_id'])
            try:
                active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
                active_session.allow_notif = True
                active_session.save()
                return Response(data=None, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed in body!')

    def disable_notif(self, request):
        seri = self.serializer_class(data=request.data)
        if seri.is_valid():
            chat_id = int(seri.validated_data['chat_id'])
            try:
                active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
                active_session.allow_notif = False
                active_session.save()
                return Response(data=None, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed in body!')

    def find_admins_to_send_notif(self, request):
        admins = TelegramActiveSessions.objects.filter(allow_notif=True, user__is_staff=True)
        chat_id_list = [admin.chat_id for admin in admins]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)

class AdminQuestionAnswerView(ViewSet):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]
    answer_serializer = AnswerSerializer
    question_update_message_serializer = ChatIdMessageIdSerializer
    question_answer_serializer = QuestionAnswerSerializer

    def get_question(self, request, q_id=None):
        try:
            question = QuestionAnswer.objects.get(pk=q_id)
            seri = self.question_answer_serializer(question)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except QuestionAnswer.DoesNotExist:
            return NotFound(detail=f'Question id={q_id} not found!')

    def get_all_questions(self, request):
        answered = request.GET.get('answered', False)
        questions = None
        print(answered)
        if answered == 'True':
            print('.')
            questions = QuestionAnswer.objects.filter(~Q(answer=''))
        else:
            print('*')
            questions = QuestionAnswer.objects.filter(answer='')
        seri = self.question_answer_serializer(questions, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def answer_question(self, request, q_id=None):
        seri = self.answer_serializer(data=request.data)
        if seri.is_valid():
            question = QuestionAnswer.objects.get(pk=q_id)
            answer = seri.validated_data.get('answer')    
            question.answer = answer
            question.save()
            seri = self.question_answer_serializer(question)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        raise ValidationError(detail=seri.errors)

    @transaction.atomic
    def update_question_message(self, request, q_id):
        seri = self.question_update_message_serializer(data=request.data, many=True)
        if seri.is_valid():
            try:
                question = QuestionAnswer.objects.get(pk=q_id)

                for data in seri.validated_data:
                    chat_id = str(data['chat_id'])
                    message_id = str(data['message_id'])

                    # Check if the chat_id is added before
                    all_questions = redis_instance.get(chat_id)
                    all_questions = '' if all_questions is None else all_questions.decode('utf-8')    
                        
                    key = f"{chat_id};{q_id}"
                    # If the question is added before
                    if str(question.id) in all_questions:
                        message_id_list = redis_instance.get(key)
                        message_id_list = '' if  message_id_list is None else message_id_list.decode('utf-8')
                        
                        if message_id not in message_id_list:
                            redis_instance.set(key, f"{message_id_list}{message_id}|")
                            redis_instance.set(chat_id, f"{all_questions}{message_id}|")
                    else:
                        redis_instance.set(chat_id, f"{all_questions}{message_id}|")
                        redis_instance.set(key, message_id)

                    redis_instance.set(f"{chat_id}|{message_id}", f'{q_id}')


                return Response(data=None, status=status.HTTP_200_OK)

            except QuestionAnswer.DoesNotExist:
                raise NotFound(detail=f'Question(id = {q_id}) not found!')

        raise ValidationError(detail=seri.errors)

    def get_questions_in_chat(self, request):
        chat_id = request.GET.get('chat_id', None)
        if chat_id is None:
            raise ValidationError('Chat id must be sent');

        message_id_list = redis_instance.get(chat_id)
        if message_id_list is None:
            return Response(data=dict(), status=status.HTTP_200_OK)
        
        output = dict()
        message_id_list = message_id_list.decode('utf-8').split('|')
        for i in range(len(message_id_list) - 1):
            message_id = message_id_list[i]
            question_id = redis_instance.get(f"{chat_id}|{message_id}")
            output[message_id] = int(question_id.decode('utf-8'))

        return Response(data=output, status=status.HTTP_200_OK)

class MemberQuestionAnswerView(ViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = QuestionAnswerSerializer

    def get_question_answer(self, request, q_id):
        try:
            question_answer = QuestionAnswer.objects.get(pk=q_id)
            seri =  self.serializer_class(question_answer)
            return Response(data=seri.data, status=status.HTTP_200_OK)
            
        except QuestionAnswer.DoesNotExist:
            raise NotFound(detail=f'Question(id= {q_id}) not found!')

    def get_my_questions(self, request):
        questions = QuestionAnswer.objects.filter(user=request.user)
        seri = self.serializer_class(questions, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)