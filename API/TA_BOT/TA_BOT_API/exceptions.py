from rest_framework.exceptions import APIException

class UserAlreadyExistsException(APIException):
    status_code = 400
    default_detail = 'A user with this email already exists!'
    default_code = 'bad_request'


class NoOtpException(APIException):
    status_code = 400
    default_detail = 'You have not requested an otp yet!'
    default_code = 'bad_request'

class InvalidSecretKey(APIException):
    status_code = 400
    default_detail = 'Entered secret is not correct!'
    default_code = 'bad_request'

class OtpMismatchException(APIException):
    status_code = 400
    default_detail = 'Otp is not correct!'
    default_code = 'bad_request'