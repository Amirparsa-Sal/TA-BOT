from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinLengthValidator
from django.db.models.base import Model

# Create your models here.

class AuthData(models.Model):

    student_id = models.CharField(max_length=16, null=False)
    email = models.EmailField(unique=True, null=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Auth Data"

class UserManager(BaseUserManager):

    def create_user(self, email, first_name, last_name, password, student_id=None):
        if not email:
            raise ValueError('Users must have an email address.')
        if not password:
            raise ValueError('Users must have a password.')

        email = self.normalize_email(email)
        user = self.model(email=email,first_name=first_name, last_name=last_name, student_id=student_id)
        user.set_password(password)
        user.is_active = False
        
        user.save(using=self._db)
        return user

    def create_superuser(self,email, password, first_name=None, last_name=None, is_superuser=True):
        user = self.create_user(email, first_name, last_name, password)
        user.set_password(password)
        user.is_active = True
        user.is_superuser = is_superuser
        user.is_staff = True

        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    student_id = models.CharField(max_length=16, null=True)
    is_active = models.BooleanField(default=False) #if the account is activated
    is_staff = models.BooleanField(default=False) #if is admin

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class TelegramActiveSessions(models.Model):
    chat_id = models.BigIntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    allow_notif = models.BooleanField(default=False)
    
class Category(models.Model):
    title = models.CharField(max_length=64)
    is_taught = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"

class Resource(models.Model):
    category = models.ForeignKey(Category, related_name='resources', on_delete=models.CASCADE)
    title = models.CharField(max_length=128,null=False,blank=False)
    link = models.CharField(max_length=1024)
    
class Grade(models.Model):
    link = models.CharField(max_length=1024)
    published = models.BooleanField(default=False)

def homework_file_directory_path(instance, filename):
    return f'{instance.title}/{filename}'

class HomeWork(models.Model):
    title = models.CharField(max_length=64)
    # file = models.FileField(upload_to=homework_file_directory_path, blank=True, null=True)
    file_id = models.CharField(max_length=128, blank=True)
    grade = models.OneToOneField(Grade, on_delete=models.SET_NULL, null=True)
    due_date_time = models.DateTimeField()
    published = models.BooleanField(default=False)

class QuestionAnswer(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    question = models.TextField(blank=False)
    answer = models.TextField(blank=True)
    category = models.ForeignKey(Category, null=False, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    source_chat_id = models.BigIntegerField()
