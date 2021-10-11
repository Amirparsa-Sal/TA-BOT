from django.core.validators import MinLengthValidator, validate_integer
from django.db.models import fields
from rest_framework import serializers
from django.core.validators import MinLengthValidator,MaxLengthValidator,DecimalValidator
from .models import Category, HomeWork, Resource, Grade

class UserRegisterSerializer(serializers.Serializer):
    '''A serializer to get inputs of user registeration api. It recieves email and chat_id as inputs.'''
    email = serializers.EmailField()

    def validate(self, attrs):
        '''Check if the student_id is valid.'''
        if attrs['email'][-10:] == '@aut.ac.ir':
            return super().validate(attrs)
        raise serializers.ValidationError(detail='Student email is not valid!')

class AccountActivitionSerializer(serializers.Serializer):
    '''A serializer to get inputs of acccount activision api. It recieves chat_id and otp as inputs.'''
    email = serializers.EmailField()
    otp = serializers.CharField(validators=[validate_integer, MinLengthValidator(5), MaxLengthValidator(5)])

class AdminRegisterSerializer(serializers.Serializer):
    '''This is a serializer for admin registeration. it recieves email,chat_id and secret key as inputs.'''
    email = serializers.EmailField()
    secret = serializers.CharField()

class ChatIdSerializer(serializers.Serializer):
    '''This is a serializer for logout. it receives a chat_id to remove it from user active sessions.'''
    chat_id = serializers.IntegerField()

class CategorySerilizer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'
        read_only_fields = ['category']

class ResourcePartialUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    link = serializers.CharField(required=False)

class HomeWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeWork
        fields = ['id','title','file','published','due_date_time']
        read_only_fields = ['id']

class HomeWorkPartialUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    file = serializers.FileField(required=False)
    published = serializers.BooleanField(required=False)
    due_date_time = serializers.DateTimeField(required=False)

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ['id']