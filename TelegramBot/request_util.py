from enum import Enum
import requests

class ApiUrls(Enum):

    BASE_URL = 'http://127.0.0.1:8000/api/'

    # Auth Urls
    AUTH_BASE = BASE_URL + 'auth/'
    SEND_OTP = AUTH_BASE + 'send-otp/'
    ACTIVATE_ACCOUNT = AUTH_BASE + 'activate-account/'
    REGISTER_ADMIN = AUTH_BASE + 'register-admin/'
    LOGIN = AUTH_BASE + 'login/'
    LOGOUT = AUTH_BASE + 'logout/'

def post(url, **kwargs):
    # Creating response body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, data=data)
    return response.json(), response.status_code

def post_with_auth(url, auth_token, **kwargs):
    # Creating response body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, data=data, headers={'Authorization':f'Token {auth_token}'})
    return response.json(), response.status_code