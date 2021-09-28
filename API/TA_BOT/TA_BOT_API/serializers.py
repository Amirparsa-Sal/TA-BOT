from django.core.validators import MinLengthValidator, validate_integer
from rest_framework import serializers
from django.core.validators import MinLengthValidator,MaxLengthValidator,DecimalValidator

class UserRegisterSerializer(serializers.Serializer):
    '''A serializer to get inputs of user registeration api. It recieves email and chat_id as inputs.'''
    email = serializers.EmailField()
    chat_id = serializers.IntegerField()

    def validate(self, attrs):
        '''Check if the student_id is valid.'''
        if attrs['email'][-10:] == '@aut.ac.ir':
            return super().validate(attrs)
        raise serializers.ValidationError(detail='Student email is not valid!')

class AccountActivitionSerializer(serializers.Serializer):
    '''A serializer to get inputs of acccount activision api. It recieves chat_id and otp as inputs.'''
    chat_id = serializers.IntegerField()
    otp = serializers.CharField(validators=[validate_integer, MinLengthValidator(5), MaxLengthValidator(5)])