from django.core.validators import MinLengthValidator, validate_integer
from django.db.models import fields
from rest_framework import serializers
from django.core.validators import MinLengthValidator,MaxLengthValidator,DecimalValidator
from .models import Category

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
