from enum import Enum
import requests
import re
import os
from file_utils import get_file_name
import environ

env = environ.Env()
environ.Env.read_env()

class ApiUrls(Enum):
    '''An enum for request urls'''
    
    BASE_URL = f"http://{env('API_HOST')}:8000/"

    BASE_API_URL = BASE_URL + 'api/'

    ###### Auth Urls
    AUTH_BASE = BASE_API_URL + 'auth/'
    SEND_OTP = AUTH_BASE + 'send-otp/'
    ACTIVATE_ACCOUNT = AUTH_BASE + 'activate-account/'
    REGISTER_ADMIN = AUTH_BASE + 'register-admin/'
    LOGIN = AUTH_BASE + 'login/'
    LOGOUT = AUTH_BASE + 'logout/'
    LAST_LOGIN = AUTH_BASE + 'last-login/'
    ACTIVE_SESSIONS = AUTH_BASE + 'active-sessions/'
    ALL_STUDENTS_SESSIONS = AUTH_BASE + 'all-students-sessions/'
    ALL_ADMINS_SESSIONS = AUTH_BASE + 'all-admins-sessions/'

    ###### Member Urls

    MEMBER_BASE_URL = BASE_API_URL + 'member/'
    # Member Categories
    MEMBER_CATEGORY_ROOT = MEMBER_BASE_URL + 'categories/'
    MEMBER_CATEGORY_RESOURCES = MEMBER_BASE_URL + 'categories/{id}/resources/'
    MEMBER_CATEGORY_ADD_QUESTION = MEMBER_BASE_URL + 'categories/{id}/questions/'

    # Member Homeworks
    MEMBER_HOMEWORK_ROOT = MEMBER_BASE_URL + 'homeworks/'
    MEMBER_HOMEWORK_WITH_ID = MEMBER_BASE_URL + 'homeworks/{id}/'
    MEMBER_HOMEWORK_GRADES = MEMBER_BASE_URL + 'homeworks/{id}/grades/'

    ###### Admin Urls
    ADMIN_BASE_URL = BASE_API_URL + 'admin/'
    # Admin Homeworks
    ADMIN_HOMEWORK_ROOT = ADMIN_BASE_URL + 'homeworks/'
    ADMIN_HOMEWORK_WITH_ID = ADMIN_BASE_URL + 'homeworks/{id}/'
    ADMIN_HOMEWORK_GRADE = ADMIN_BASE_URL + 'homeworks/{id}/grade/'
    ADMIN_HOMEWORK_GRADE_PUBLISH = ADMIN_BASE_URL + 'homeworks/{id}/grade/publish/'
    ADMIN_HOMEWORK_GRADE_UNPUBLISH = ADMIN_BASE_URL + 'homeworks/{id}/grade/unpublish/'

    # Admin Category
    ADMIN_CATEGORY_ROOT = ADMIN_BASE_URL + 'categories/'
    ADMIN_CATEGORY_TOGGLE_STATUS = ADMIN_BASE_URL + 'categories/{id}/toggle-status/'
    ADMIN_CATEGORY_RESOURCES = ADMIN_BASE_URL + 'categories/{id}/resources/'

    # Admin Resource
    ADMIN_RESOURCES_WITH_ID  = ADMIN_BASE_URL + 'resources/{id}/' 

    # Admin Incoming Notifs
    ADMIN_INCOMING_NOTIF_STATUS  = ADMIN_BASE_URL + 'incoming-notifs/status/'
    ADMIN_INCOMING_NOTIF_ENABLE  = ADMIN_BASE_URL + 'incoming-notifs/enable/'
    ADMIN_INCOMING_NOTIF_DISABLE  = ADMIN_BASE_URL + 'incoming-notifs/disable/'

    # ADMIN QUESTION ANSWER
    ADMIN_QUESTION_ANSWER_ANSWER = ADMIN_BASE_URL + 'question-answer/{id}/answer/'
    ADMIN_QUESTION_ANSWER_GET_DATA = ADMIN_BASE_URL + 'question-answer/get-chat-data/'
    ADMIN_QUESTION_ANSWER_WITH_ID = ADMIN_BASE_URL + 'question-answer/{id}/'
    ADMIN_QUESTION_ANSWER_ROOT = ADMIN_BASE_URL + 'question-answer/'

    # MEMBER QUESTION ANSWER
    MEMBER_QUESTION_ANSWER_WITH_ID = MEMBER_BASE_URL + 'question-answer/{id}/'
    MEMBER_MY_QUEESTIONS = MEMBER_BASE_URL + 'question-answer/my-questions/'

def post(url, **kwargs):
    '''Posts data with request body.'''
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, data=data)
    return response.json() if response.content else None, response.status_code

def post_with_auth(url, auth_token, **kwargs):
    '''Posts data with request body with authorization token'''
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    response = requests.post(url, json=data, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code

def get_with_auth(url, auth_token, **kwargs):
    '''Sends a get request with authorization token.'''
    # Creating query params
    params = dict()
    for key,value in kwargs.items():
        params[key] = value
    # Sending the request
    response = requests.get(url, headers={'Authorization':f'Token {auth_token}'}, params=params)
    return response.json() if response.content else None, response.status_code

def get(url, **kwargs):
    '''Sends a get request to url.'''
    # Creating query params
    params = dict()
    for key,value in kwargs.items():
        params[key] = value
    # Sending the request
    response = requests.get(url, params=params)
    return response.json() if response.content else None, response.status_code


def getFilename_fromCd(cd):
    '''A util function to get file name from Content-Disposition header'''
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0][1:-1]

def get_file(relative_url):
    '''Gets file from relative_url to file.'''
    response = requests.get(f'{ApiUrls.BASE_URL.value}{relative_url}', allow_redirects=True)
    filename = getFilename_fromCd(response.headers.get('Content-Disposition'))
    if not os.path.exists('downloads'):
        os.mkdir('downloads')
    with open(f'downloads/{filename}', 'wb') as file:
        file.write(response.content)
    
    return f'downloads/{filename}'

def patch_with_auth_and_body(url, auth_token, body:dict):
    '''Sends a patch request with authorization token and takes the whole request body to send.'''
    # Sending the request
    response = requests.patch(url, data=body, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code

def patch_with_auth(url, auth_token, **kwargs):
    '''Sends a patch request with authorization token.'''
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    return patch_with_auth_and_body(url, auth_token, data)

def delete_with_auth(url, auth_token):
    '''Sends a delete request to url with authorization token.'''
    response = requests.delete(url, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code

def put_with_auth_and_body(url, auth_token, body):
    response = requests.put(url, json=body, headers={'Authorization':f'Token {auth_token}'})
    return response.json() if response.content else None, response.status_code

def put_with_auth(url, auth_token, **kwargs):
    '''Sends a put request to url with authorization token.'''
    # Creating request body
    data = dict()
    for key,value in kwargs.items():
        data[key] = value
    # Sending the request
    return put_with_auth_and_body(url, auth_token, data)

def multipart_form_data(url, auth_token, body:dict, method ='POST', file_address=None, file_field_name='file', **kwargs):
    multipart_form_data = dict()
    for key,value in body.items():
        multipart_form_data[key] = ('', value)
    # Create file field in multipart form data if needed
    file = None
    if file_address:
        file = open(file_address, 'rb')
        multipart_form_data[file_field_name] = (get_file_name(file_address), file)

    # Send request
    if method == 'POST':
        response = requests.post(url, files=multipart_form_data)
    elif method == 'PUT':
        response = requests.put(url, files=multipart_form_data)
    elif method == 'PATCH':
        response = requests.patch(url, files=multipart_form_data)
    else:
        raise ValueError('Method not allowed!')
    
    if file:
        file.close()

    return response.json() if response.content else None, response.status_code