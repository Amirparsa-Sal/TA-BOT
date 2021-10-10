from enum import Enum
import requests
import re
import os

class ApiUrls(Enum):

    BASE_URL = 'http://127.0.0.1:8000'

    BASE_API_URL = 'http://127.0.0.1:8000/api/'

    ###### Auth Urls
    AUTH_BASE = BASE_API_URL + 'auth/'
    SEND_OTP = AUTH_BASE + 'send-otp/'
    ACTIVATE_ACCOUNT = AUTH_BASE + 'activate-account/'
    REGISTER_ADMIN = AUTH_BASE + 'register-admin/'
    LOGIN = AUTH_BASE + 'login/'
    LOGOUT = AUTH_BASE + 'logout/'
    LAST_LOGIN = AUTH_BASE + 'last-login'

    ###### Member Urls

    MEMBER_BASE_URL = BASE_API_URL + 'member/'
    # Member Categories
    MEMBER_GET_CATEGORIES = MEMBER_BASE_URL + 'categories'

    ###### Admin Urls
    ADMIN_BASE_URL = BASE_API_URL + 'admin/'
    # Admin Homeworks
    ADMIN_HOMEWORK_ROOT = ADMIN_BASE_URL + 'homeworks/'
    ADMIN_HOMEWORK_WITH_ID = ADMIN_BASE_URL + 'homeworks/{id}/'
    ADMIN_HOMEWORK_GRADE_PUBLISH = ADMIN_BASE_URL + 'homeworks/{id}/grade/publish/'
    ADMIN_HOMEWORK_GRADE_UNPUBLISH = ADMIN_BASE_URL + 'homeworks/{id}/grade/unpublish/'

def post(url, **kwargs):
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, data=data)
    return response.json() if response.content else None, response.status_code

def post_with_auth(url, auth_token, **kwargs):
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, data=data, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code

def get_with_auth(url, auth_token, **kwargs):
    # Creating query params
    params = dict()
    for key,value in kwargs.items():
        params[key] = value
    # Sending the request
    response = requests.get(url, headers={'Authorization':f'Token {auth_token}'}, params=params)
    return response.json() if response.content else None, response.status_code

def get(url, **kwargs):
    # Creating query params
    params = dict()
    for key,value in kwargs.items():
        params[key] = value
    # Sending the request
    response = requests.get(url, params=params)
    return response.json() if response.content else None, response.status_code


def getFilename_fromCd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0][1:-1]

def get_file(relative_url):
    response = requests.get(f'{ApiUrls.BASE_URL.value}{relative_url}', allow_redirects=True)
    filename = getFilename_fromCd(response.headers.get('Content-Disposition'))
    if not os.path.exists('downloads'):
        os.mkdir('downloads')
    with open(f'downloads/{filename}', 'wb') as file:
        file.write(response.content)
    
    return f'downloads/{filename}'

def patch_with_auth(url, auth_token, **kwargs):
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request

    response= requests.patch(url, data=data, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code