from rest_framework.exceptions import APIException

class UserAlreadyExistsException(APIException):
    status_code = 400
    default_detail = 'A user with this email already exists!'
    default_code = 'bad_request'


class NoOtpException(APIException):
    status_code = 400
    default_detail = 'You have not requested an otp yet!'
    default_code = 'bad_request'