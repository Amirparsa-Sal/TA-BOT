from os import stat
from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q
from django.utils.crypto import get_random_string
from django.conf import settings
from django.db.models import Q

from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.authtoken.models import Token


from .serializers import AnswerSerializer, ChatIdMessageIdSerializer, GradeSerializer, QuestionAnswerSerializer, QuestionSerializer, ResourcePartialUpdateSerializer, UserRegisterSerializer, AccountActivitionSerializer,AdminRegisterSerializer, \
    ChatIdSerializer, CategorySerilizer, ResourceSerializer, HomeWorkSerializer, HomeWorkPartialUpdateSerializer \

from .models import AuthData, Category, Grade, QuestionAnswer, TelegramActiveSessions, Resource, HomeWork
from .exceptions import UserAlreadyExistsException,NoOtpException,InvalidSecretKey, OtpMismatchException, AuthDataNotFoundException
from .utils import send_email

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from django.db import transaction

import redis

user_model = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,port=settings.REDIS_PORT, db=0)
secret = getattr(settings, 'SECRET_KEY', 'thikiuridi')

from rest_framework.authtoken.models import Token

class BotMetaDataView(ViewSet):
    '''
        This is a view to get some meta data about users.\n
        The data is mostly about users sessions.
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_last_login(self, request):
        '''
        GET: Checks the last login for a specific chat_id and returns the token if exists.\n 
        This is used to keep user logged in when the bot restarts.
        '''
        # Get chat_id from query params
        chat_id = request.GET.get('chat_id', None)
        # If chat_id is not given: raise error
        if chat_id is None:
            raise ValidationError(detail='chat_id is not in request params!')
        # Find the active session if exists
        try:
            active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
            # Retrieve the token
            token = Token.objects.get(user=active_session.user)
            return Response(data={'token': token.key, 'is_admin':active_session.user.is_staff}, status=status.HTTP_200_OK) 
        except TelegramActiveSessions.DoesNotExist:
            # Return Nothing if there is no active session
            return Response(data={'token': None}, status=status.HTTP_200_OK)

    def get_all_active_sessions(self, request):
        '''
        GET: Checks for all active chat_ids for a user and returns all of them.\n
        This is used when we want to send notifications to all logged in sessions for a user.
        '''
        # Get user_id from query params
        user_id = request.GET.get('user_id', None)
        # If user_id is not given: raise error
        if user_id is None:
            raise ValidationError(detail='user_id is not in request params!')
        # Find all active sessions
        active_sessions = TelegramActiveSessions.objects.filter(user__id=user_id)
        # Retrieve all chat_ids
        chat_id_list = [session.chat_id for session in active_sessions]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)
    
    def get_all_students_sessions(self, request):
        '''
        GET: Checks for all active chat_ids which are logged in as a student.
        This is used when we want to send notifications to all students or to answer their questions.
        '''
        # Find all active sessions
        active_sessions = TelegramActiveSessions.objects.filter(user__is_staff=False)
        # Retrieve all chat_ids
        chat_id_list = [session.chat_id for session in active_sessions]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)

    def get_all_admin_sessions(self, request):
        '''
        GET: Checks for all active chat_ids which are logged in as an admin and allow notif.
        This is used when we want to send students questions to all admins.
        '''
        admins = TelegramActiveSessions.objects.filter(allow_notif=True, user__is_staff=True)
        chat_id_list = [admin.chat_id for admin in admins]
        return Response(data=chat_id_list, status=status.HTTP_200_OK)

    
class CustomAuthToken(ObtainAuthToken):
    ''' This is a view for login.'''

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        '''POST: Returns a token and is_admin after login by user.'''
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
    '''This is a view for authentication stuff.'''
    authentication_classes = [TokenAuthentication]
    
    def register_user(self, request):
        '''POST: Sends the otp password to the given email if the email is not registered.'''
        seri = UserRegisterSerializer(data=request.data)
        # Checking if the email is valid
        if seri.is_valid():
            email = seri.validated_data.get('email')

            # Checking if the email already exsits in redis keys
            otp = redis_instance.get(email.lower())
            if otp is None:
                # Checking if the user has registered before
                try:
                    user = user_model.objects.get(email__iexact=email)
                    # Checking if the user has activated his/her account already
                    if user.is_active:
                        raise UserAlreadyExistsException(detail='یه کاربر قبلا با این ایمیل ثبت نام کرده! یه ایمیل دیگه وارد کن!')
                except user_model.DoesNotExist:
                    # Create a new user if user does not exist
                    try:
                        auth_data = AuthData.objects.get(email__iexact=email)
                        user_model.objects.create_user(email, auth_data.first_name, auth_data.last_name, auth_data.password, student_id=auth_data.student_id)
                    except AuthData.DoesNotExist:
                        raise AuthDataNotFoundException(detail='اطلاعات مربوط به این ایمیل در بات ثبت نشده! لطفا دوباره ایمیل رو وارد کن!')
            
            # Create OTP and save in redis
            otp = get_random_string(length=5, allowed_chars='0123456789')
            redis_instance.set(name=email.lower(), value=otp, ex= 60 * 5)
            
            try:
                send_email(
                    email_host=settings.EMAIL_HOST,
                    host_port=settings.EMAIL_PORT,
                    sender_email=settings.EMAIL_SENDER,
                    password=settings.EMAIL_PASSWORD,
                    receiver_email=email,
                    subject=settings.EMAIL_SUBJECT,
                    message=settings.EMAIL_MESSAGE_FORMAT.format(otp=otp)
                )
            except Exception as e:
                raise APIException('Failed to send the email!')
            
            return Response(data={}, status=status.HTTP_200_OK)
        raise ValidationError(detail='The data is not valid!')

    def activate_account(self, request):
        '''POST: Activates the account if the email and otp are valid.'''
        seri = AccountActivitionSerializer(data=request.data)
        # Checking if the request data is valid
        if seri.is_valid():
            # Getting request data
            email = seri.validated_data.get('email')
            given_otp = seri.validated_data.get('otp')

            # Checking if the user has requested an otp
            otp = redis_instance.get(email)
            if otp is None:
                raise NoOtpException(detail='شما تا حالا درخواست فرستادن رمز یک بار مصرف ندادید!')
            # Checking if the otp is correct
            if given_otp != otp.decode('utf-8'):
                raise OtpMismatchException(detail='رمز یک بار مصرف وارد شده اشتباهه! لطفا دوباره واردش کن!')

            # Activate account
            user = user_model.objects.get(email__iexact=email)
            user.is_active = True
            user.save()

            # Delete email from redis
            redis_instance.delete(email)
            
            return Response(data={}, status=status.HTTP_200_OK)

        raise ValidationError(detail='The data is not valid!')

    def register_admin(self, request):
        '''
        POST: registers an admin using an email and a secret key.\n
        The secret key is placed in .env file in TA_BOT folder.
        '''
        seri = AdminRegisterSerializer(data=request.data)
        # Checking if the request data is valid
        if seri.is_valid():
            # Getting request data
            email = seri.validated_data.get('email')
            given_secret = seri.validated_data.get('secret')

            # Checking if the secret key is correct
            if given_secret != secret:
                raise InvalidSecretKey(detail='رمز وارد شده اشتباهه! دوباره واردش کن!')
            
            # Checking if a user with that email already exists
            try:
                user_model.objects.get(email__iexact=email)
                raise UserAlreadyExistsException(detail='یه کاربر با این ایمیل تو بات وجود داره! یه ایمیل دیگه وارد کن!')
            except user_model.DoesNotExist:
                user_model.objects.create_superuser(email, secret)

            return Response(data={}, status=status.HTTP_200_OK) 
        
        raise ValidationError(detail='The data is not valid!')

    def logout(self, request):
        '''POST: Logs out from the account. It deletes the active session corresponding to that chat_id.'''
        seri = ChatIdSerializer(data=request.data)
        if seri.is_valid():
            chat_id = seri.validated_data.get('chat_id')
            
            # Delete chat_id from user sessions
            user = request.user
            user.active_sessions.filter(chat_id=chat_id).delete()

            return Response(data={}, status=status.HTTP_200_OK) 
        
        raise ValidationError(detail='The data is not valid!')
        

class MemberCategoryView(ViewSet):
    '''This is a view for course syllabes for students. We call them category.'''
    authentication_classes = [TokenAuthentication]
    serializer_class = CategorySerilizer
    resource_serializer_class = ResourceSerializer
    question_serializer_class = QuestionSerializer
    question_answer_serializer_class =QuestionAnswerSerializer
    
    def get_all_categories(self, request):
        '''GET: Returns all categories as a list.'''
        categories = Category.objects.all()
        seri = self.serializer_class(categories, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def get_resources(self, request, cat_id):
        '''GET: Returns all resourceasa within a category given the cat_id.'''
        try:
            # Find the category
            category = Category.objects.get(pk=cat_id)
            # Making a list of resources
            resources = list(category.resources.all())
            seri = ResourceSerializer(resources, many=True)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

    @transaction.atomic
    def add_question(self, request, cat_id):
        '''POST: Adds a question to the category given the cat_id and question.'''
        seri = self.question_serializer_class(data=request.data)
        # Checking if the question is valid
        if seri.is_valid():
            try:
                # Finding the category
                category = Category.objects.get(pk=cat_id)
                # Creating the question
                question_answer = QuestionAnswer(question=seri.validated_data['question'], source_chat_id=seri.validated_data['chat_id'], user=request.user, category=category)
                question_answer.save()
                seri = self.question_answer_serializer_class(question_answer)
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except Category.DoesNotExist:
                raise NotFound(detail=f'Category(id = {cat_id}) not found!')
        raise ValidationError(detail=seri.errors)

class AdminCategoryView(ViewSet):
    '''This is a view for course syllabes for admins. We call them category.'''
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = CategorySerilizer

    def get_all_categories(self, request):
        '''GET: Returns all categories as a list.'''
        categories = Category.objects.all()
        seri = self.serializer_class(categories, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def change_category_status(self, request, cat_id=None):
        '''
        PUT: Changes the category status.\n 
        if is_taught is true then it will be false and vice versa.
        '''
        # Checking if the category exists
        try:
            category = Category.objects.get(pk=cat_id)
            # Toggle is_taught field
            category.is_taught = not category.is_taught
            category.save()
            seri = self.serializer_class(category)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

    def add_resource(self, request, cat_id):
        '''POST: Adds a resource to the category given its cat_id and resource details.'''
        seri = ResourceSerializer(data=request.data)
        # Checking if the resource details is valid
        if seri.is_valid():
            # Checking if the category exists
            try:
                category = Category.objects.get(pk=cat_id)
                # Creating the resource
                resource = Resource(title=seri.validated_data.get('title'), \
                                    link=seri.validated_data.get('link'),
                                    category=category)
                resource.save()
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except Category.DoesNotExist:
                raise NotFound(detail=f'Category(id = {cat_id}) not found!')
        raise ValidationError(detail='The data is not valid!')
        

    def get_all_resources(self, request, cat_id):
        '''GET: Returns all resourceasa within a category given the cat_id.'''
        # Checking if the category exists
        try:
            category = Category.objects.get(pk=cat_id)
            # Making a list of resources
            resources = list(category.resources.all())
            seri = ResourceSerializer(resources, many=True)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            raise NotFound(detail=f'Category(id = {cat_id}) not found!')

class AdminResourceView(ViewSet):
    '''This is a view for resources for admin.'''
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = ResourceSerializer

    def get_resource(self, request, res_id):
        '''GET: Gets details of a resource given its res_id.'''
        # Checking if the resource ecisrs
        try:
            res = Resource.objects.get(pk=res_id)
            # Serializing the resource
            seri = self.serializer_class(res)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except Resource.DoesNotExist:
            raise NotFound(detail=f'Resource(id = {res_id}) not found!')

    def update_resource(self, request, res_id):
        '''PATCH: Partially updates the details of a resource given its res_id.'''
        seri = ResourcePartialUpdateSerializer(data=request.data)
        # Checking of the reqiest data is valid
        if seri.is_valid():
            # Checking if the resource exists
            try:
                res = Resource.objects.get(pk=res_id)
                # Partially update the fields
                res.title = seri.validated_data.get('title', res.title)
                res.link = seri.validated_data.get('link', res.link)
                res.save()
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except Resource.DoesNotExist:
                raise NotFound(detail=f'Resource(id = {res_id}) not found!')
        raise ValidationError(detail='The data is not valid!')
        

    def delete_resource(self, request, res_id):
        '''DELETE: deletes a resource given its res_id.'''
        # Checking if the resource exists
        try:
            res = Resource.objects.get(pk=res_id)
            # Delete the resource
            res.delete()
            return Response(data=None, status=status.HTTP_200_OK)
        except Resource.DoesNotExist:
            raise NotFound(detail=f'Resource(id = {res_id}) not found!')

class AdminHomeWorkView(ViewSet):
    '''This is a view for admins to manage homeworks.'''
    queryset = HomeWork.objects.all()
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = HomeWorkSerializer
    update_serializer_class = HomeWorkPartialUpdateSerializer
    grade_serializer_class = GradeSerializer

    def get_homework(self, request, hw_id=None):
        '''GET: Gets the details of a homework given its hw_id.'''
        # Checking if the homework exists
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            seri = self.serializer_class(hw)
            data = seri.data
            # Adding grade link to details
            data['grade_link'] = hw.grade.link if hw.grade else None
            return Response(data=data, status=status.HTTP_200_OK)
        except:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')
    
    def get_all_homeworks(self, request):
        '''GET: Gets all homeworks and returns a list of them.'''
        homeworks = HomeWork.objects.all()
        seri = self.serializer_class(homeworks, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def create_homework(self, request):
        '''POST: Creates a new homework given its details.'''
        seri = self.serializer_class(data=request.data)
        # Checking if the data is valid
        if seri.is_valid():
            # Creating the homework
            hw = HomeWork(title=seri.validated_data.get('title'), \
                          file_id=seri.validated_data.get('file_id'), \
                          published=seri.validated_data.get('published'), \
                          due_date_time=seri.validated_data.get('due_date_time'))
            hw.save()
            seri = self.serializer_class(hw)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        raise ValidationError(detail='The data is not valid!')

    def delete_homework(self, request, hw_id=None):
        '''DELETE: Deletes the homework given its hw_id.'''
        HomeWork.objects.filter(pk=hw_id).delete()
        return Response(data=None, status=status.HTTP_200_OK)

    def update_homework(self, request, hw_id=None):
        '''PATCH: Partially updates the homework given its hw_id and details.'''
        seri = self.update_serializer_class(data=request.data)
        # Checking if the data is valid
        if seri.is_valid():
            # Checking if the hw exists
            try:
                hw = HomeWork.objects.get(pk=hw_id)
                # Partially update the fields
                hw.title = seri.validated_data.get('title',hw.title)
                hw.file_id = seri.validated_data.get('file_id', hw.file_id)
                hw.due_date_time = seri.validated_data.get('due_date_time', hw.due_date_time)
                hw.published = seri.validated_data.get('published', hw.published)
                hw.save()
                seri = self.serializer_class(hw)
                return Response(data=seri.data, status=status.HTTP_200_OK)
            except HomeWork.DoesNotExist:
                raise NotFound(detail=f'homework(id= {hw_id}) not found!')
        raise ValidationError(detail='The data is not valid!')

    def update_grade(self, request, hw_id=None):
        '''PUT: Updates the grade of a homework given the hw_id and grade details.'''
        seri = self.grade_serializer_class(data=request.data)
        # Checking if the request data is valid
        if seri.is_valid():
            # Checking if the homework exists.
            try:
                hw = HomeWork.objects.get(pk=hw_id)
                grade = hw.grade
                # Update the grade if exists
                if grade is not None:
                    grade.link = seri.validated_data.get('link')
                    grade.published = seri.validated_data.get('published')
                    grade.save()
                # Creeate the grade if not exists
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
        '''DELETE: Deletes the homework given its hw_id.'''
        # Checking if the homework exists
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            # Delete the grade
            hw.grade.delete()
            hw.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def get_grade(self ,request, hw_id=None):
        '''GET: Gets the details of the grade given its hw_id.'''
        # Checking if the hw exists
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            grade = hw.grade
            # Raise not found if there is no grade for this hw
            if grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            # Return grade details if exists
            seri = self.grade_serializer_class(grade)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def publish_grade(self, request, hw_id=None):
        '''POST: Publishes the grade of a hw given its hw_id.'''
        # Checking if the hw exists
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            # Checking if the grades exists
            if hw.grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            # Publish the grade
            hw.grade.published = True
            hw.grade.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def unpublish_grade(self, request, hw_id=None):
        '''POST: Unpublishes the grade of a hw given its hw_id.'''
        # Checking if the hw exists
        try:
            hw = HomeWork.objects.get(pk=hw_id)
            # Checking if the grades exists
            if hw.grade is None:
                raise NotFound(detail=f'There is no grade for this hw!')
            # Publish the grade
            hw.grade.published = False
            hw.grade.save()
            return Response(data=None, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

class MemberHomeworkView(ViewSet):
    '''This is a view for members to work with homeworks.'''
    authentication_classes = [TokenAuthentication]
    serializer_class = HomeWorkSerializer
    grade_serializer_class = GradeSerializer

    def get_published_homeworks(self, request):
        '''GET: Gets all published homeworks.'''
        homeworks = HomeWork.objects.filter(published=True)
        seri = self.serializer_class(homeworks, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def get_homework(self, request, hw_id=None):
        '''GET: Gets a homework given its hw_id.'''
        # Checking if the hw exists and is published
        try:
            hw = HomeWork.objects.get(pk=hw_id, published=True)
            seri = self.serializer_class(hw)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except:
            raise NotFound(detail=f'homework(id= {hw_id}) not found!')

    def get_grade(self, request, hw_id):
        '''GET: Gets the grade of a homework given its hw_id.'''
        # Checking if the grade exists.
        try:
            homework = HomeWork.objects.get(pk=hw_id)
            grade = homework.grade
            # Raise not found if grade is empty or unpublished
            if grade is None or not grade.published:
                raise NotFound(detail=f'There is no grade for this hw!')
            # Return the grade if exists
            seri = self.grade_serializer_class(grade)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except HomeWork.DoesNotExist:
            raise NotFound(detail=f'Homework(id = {hw_id}) not found!')

class AdminNotificationsView(ViewSet):
    '''This is a view for admins to manage the notifications.'''
    authentication_classes = [TokenAuthentication]
    permissions_classes = [IsAdminUser]
    serializer_class = ChatIdSerializer

    def get_incoming_notif_status(self, request):
        '''GET: Gets the status of incoming notification settings. if its true the admin can recieve notifs.'''
        # Get chat_id from queery param
        chat_id = int(request.GET.get('chat_id', None))
        # Check if chat_id is given
        if chat_id is not None:
            user = request.user
            # Find the corresponding active session and turn allow_notif on
            try:
                active_session = TelegramActiveSessions.objects.get(user=user, chat_id=chat_id)
                return Response(data={'status': active_session.allow_notif}, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed!')

    def enable_notif(self, request):
        '''POST: Enables the incoming notification settings for a particular chat_id.'''        
        seri = self.serializer_class(data=request.data)
        # Checking if the request data is valid
        if seri.is_valid():
            chat_id = int(seri.validated_data['chat_id'])
            # Checking if an active session exists for that chat_id
            try:
                active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
                # Enable allow_notif
                active_session.allow_notif = True
                active_session.save()
                return Response(data=None, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed in body!')

    def disable_notif(self, request):
        '''POST: Disables the incoming notification settings for a particular chat_id.'''   
        seri = self.serializer_class(data=request.data)
        # Checking if the request data is valid
        if seri.is_valid():
            chat_id = int(seri.validated_data['chat_id'])
            # Checking if an active session exists for that chat_id
            try:
                active_session = TelegramActiveSessions.objects.get(chat_id=chat_id)
                # Enable allow_notif
                active_session.allow_notif = False
                active_session.save()
                return Response(data=None, status=status.HTTP_200_OK)
            except:
                raise NotFound('User telegram session not found!')
        raise ValidationError('Chat id must be passed in body!')

class AdminQuestionAnswerView(ViewSet):
    '''This is a view for admins to manage question answers.'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]
    answer_serializer = AnswerSerializer
    question_update_message_serializer = ChatIdMessageIdSerializer
    question_answer_serializer = QuestionAnswerSerializer

    def get_question(self, request, q_id=None):
        '''GET: Gets a question using its q_id.'''
        # Checking if the question exists
        try:
            question = QuestionAnswer.objects.get(pk=q_id)
            # Serialize the question
            seri = self.question_answer_serializer(question)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        except QuestionAnswer.DoesNotExist:
            return NotFound(detail=f'Question id={q_id} not found!')

    def get_all_questions(self, request):
        '''
        GET: Gets all questions.\n
        By default it returns non answered questions but it can be determined using query param.
        '''
        # Get answered query param. by default it is set to False.
        answered = request.GET.get('answered', False)
        questions = None
        # Get list of questions with respect to answered param.
        if answered == 'True':
            questions = QuestionAnswer.objects.filter(~Q(answer=''))
        else:
            questions = QuestionAnswer.objects.filter(answer='')
        # Serializer the question
        seri = self.question_answer_serializer(questions, many=True)
        return Response(data=seri.data, status=status.HTTP_200_OK)

    def answer_question(self, request, q_id=None):
        '''POST: create a new answer for the quesiton.'''
        seri = self.answer_serializer(data=request.data)
        # Checking if the question exists
        if seri.is_valid():
            question = QuestionAnswer.objects.get(pk=q_id)
            answer = seri.validated_data.get('answer')
            # Update the question    
            question.answer = answer
            question.save()
            seri = self.question_answer_serializer(question)
            return Response(data=seri.data, status=status.HTTP_200_OK)
        raise ValidationError(detail=seri.errors)

    @transaction.atomic
    def update_question_message(self, request, q_id):
        '''
        PUT: This function is used to update redis data to keep track of the chat_ids that have a message containing a question.\n
        We need this information to find the related question after each admin answers the question with replying to a message using the 
        /answer command.\n
        How we save informations in redis? \n
        1.Saving all message_ids which contain a questions in a chat_id:\n
        key......value\n
        'chat_id': message_id1|message_id2|message_id3\n
        2.Saving the question corresponding to a message_id in a chat_id\n
        key.................value\n
        'chat_id|message_id': q_id\n
        3.Saving the message_ids of a specific question in a chat_id.\n
        key....................value\n
        'chat_id;question_id': message_id1,message_id2,message_id3\n
        So, we get the chat_ids and message_ids to add them to the question data to identify them later.
        '''
        seri = self.question_update_message_serializer(data=request.data, many=True)
        # Checking if the request data is valid
        if seri.is_valid():
            # Checking if the question exists
            try:
                question = QuestionAnswer.objects.get(pk=q_id)

                # Update redis data
                for data in seri.validated_data:
                    chat_id = str(data['chat_id'])
                    message_id = str(data['message_id'])

                    # Check if the chat_id is added before and get all questions if exist
                    all_questions = redis_instance.get(chat_id)
                    all_questions = '' if all_questions is None else all_questions.decode('utf-8')    
                        
                    key = f"{chat_id};{q_id}"
                    # Add message_id if not exists
                    if not message_id in all_questions:
                        message_id_list = redis_instance.get(key)
                        message_id_list = '' if  message_id_list is None else message_id_list.decode('utf-8')
                        redis_instance.set(chat_id, f"{all_questions}{message_id}|")
                        redis_instance.set(key, f"{message_id_list}{message_id}|")

                    # Add question to chat_id|message_id key
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