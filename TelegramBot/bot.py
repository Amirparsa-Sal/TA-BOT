from calendar import calendar
from os import chflags, stat, stat_result
from django.core.checks import messages
from django.http import response
import telegram
from telegram import replymarkup
from telegram import message
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
import logging
import environ
import re
from request_util import *
from json import loads
from decorators import not_authorized,is_authorized,get_last_login
from keyboards import *
from date_utils import *
from file_utils import *

# Create a .env file inside the folder containing a variable named BOT_TOKEN and the value of access token.
env = environ.Env()
environ.Env.read_env()

# Setting the Token from .env file
TOKEN = env('BOT_TOKEN')

# Setting the logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
updater = Updater(token=TOKEN, use_context=True)
bot = telegram.Bot(TOKEN)

# Defining states
MEMBER_LOGGED_IN, ADMIN_LOGGED_IN, NOT_LOGGED_IN, \
REGISTER_ENTER_EMAIL, REGISTER_ENTER_OTP, LOGIN_ENTER_EMAIL, LOGIN_ENTER_PASSWORD, \
REGISTER_ADMIN_ENTER_EMAIL, REGISTER_ADMIN_ENTER_SECRET, \
ADMIN_HOMEWORKS_MAIN, ADMIN_MANAGE_HOMEWORKS, ADMIN_EACH_HOMEWORK, ADMIN_HOMEWORKS_TITLE, ADMIN_HOMEWORKS_FILE, ADMIN_HOMEWORKS_DUE_DATE,\
ADMIN_UPDATE_GRADE_ENTER_LINK, \
ADMIN_GET_CATEGORIES, ADMIN_EACH_CATEGORY, \
ADMIN_GET_RESOURCES, ADMIN_EACH_RESOURCE, ADMIN_RESOURCE_TITLE, ADMIN_RESOURCE_LINK, \
ADMIN_INCOMIG_NOTIFS, ADMIN_SEND_NOTIF, \
ADMIN_CONFIRMATION_STATE, \
ADMIN_QUESTIONS, ADMIN_EACH_QUESTION, \
MEMBER_GET_CATEGORIES, MEMBER_GET_HOMEWORKS, MEMBER_GET_HOMEWORKS_GRADE, MEMBER_ASK_QUESTION, \
MEMBER_QUESTIONS_MAIN, MEMBER_MY_QUESTIONS = range(33)

# REGEX
SIMPLE_EMAIL_REGEX = '^[^@\s]+@[^@\s]+\.[^@\s]+$'
AUT_EMAIL_REGEX = '^[A-Za-z0-9._%+-]+@aut\.ac\.ir'
OTP_REGEX = '^[0-9]{5}'
URL_REGEX = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Logout if needed
    token = context.chat_data.get('token', None)
    if token: 
        chat_id = update.effective_chat.id
        response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
    
    # Clear data and start again
    context.chat_data.clear()
    context.chat_data['is_admin'] = False
    update.message.reply_text(text='Hi! Use buttons to work with me!', reply_markup=NOT_LOGGED_IN_KEYBOARD)

    return NOT_LOGGED_IN

@get_last_login
def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Checking if user has logged in or not
    if 'token' not in context.chat_data.keys():
        update.message.reply_text(text='Operation Canceled!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN

    # Navigate to admin panel if the user is admin
    if context.chat_data['is_admin']:
        update.message.reply_text(text='Operation Canceled!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN

    # Navigate to user panel if the user is not admin
    update.message.reply_text(text='Operation Canceled!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

@get_last_login
def entry_message_handler(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This handler is for recovering user state after restarting the bot. it fills user token and navigates it to panel.'''
    token = context.chat_data.get('token', None)
    # Checking if the user had logged in
    if token is None:
        update.message.reply_text(text='Please choose one of the following options.', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN

    # Navigate to admin panel if the user is admin
    if context.chat_data['is_admin']:
        update.message.reply_text(text='Please choose one of the following options.', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    
    # Navigate to user panel if the user is not admin
    update.message.reply_text(text='Please choose one of the following options.', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN
    

def not_logged_in(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is the main entry for users who have not logged in.'''
    text = update.message.text
    # Navigate to login section
    if text == 'Login':
        update.message.reply_text(text='You are in login section. Please send your email.', reply_markup=CANCEL_KEYBOARD)
        return LOGIN_ENTER_EMAIL
    # Navigate to register section
    elif text == 'Register':
        update.message.reply_text(text='You are in register section. Please send your email.', reply_markup=CANCEL_KEYBOARD)
        return REGISTER_ENTER_EMAIL
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
    return NOT_LOGGED_IN

def admin_logged_in(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is the main entry for admins.'''
    text = update.message.text
    token = context.chat_data['token']
    # Navigate to homeworks section
    if text == 'Homeworks':
        update.message.reply_text(text='You are in homeworks section.', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
        return ADMIN_HOMEWORKS_MAIN
    elif text == 'Timeline & Resources':
        response, status = get_with_auth(ApiUrls.ADMIN_CATEGORY_ROOT.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='Categories are not provided!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        keyboard_buttons = []
        context.chat_data['categories'] = dict()
        for i,cat in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {cat['title']} {'✅' if cat['is_taught'] else '❌'}")
            context.chat_data['categories'][f"{i+1}) {cat['title']}"] = cat['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='You are in timeline & resources section. which category do you want to change?', reply_markup=keyboard)
        return ADMIN_GET_CATEGORIES
    elif text == 'Questions':
        update.message.reply_text(text='You are in questions section!', reply_markup=ADMIN_QUESTIONS_KEYBOARD)
        return ADMIN_QUESTIONS

    elif text == 'Send Notification':
        update.message.reply_text(text='Send me the text.', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_SEND_NOTIF

    elif text == 'Incoming Notifications':
        response,status = get_with_auth(ApiUrls.ADMIN_INCOMING_NOTIF_STATUS.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        update.message.reply_text(text=f"Incoming notifications are {'enabled' if response['status'] else 'disabled.'}\n\n What do you want to do?", reply_markup=ADMIN_INCOMING_NOTIFS_KEYBOARD)
        return ADMIN_INCOMIG_NOTIFS
    # Logout user
    elif text == 'Logout':
        chat_id = update.effective_chat.id
        response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN

        del context.chat_data['token']
        del context.chat_data['questions']
        context.chat_data['is_question_cache_loaded'] = False

        update.message.reply_text(text='You logged out successfully!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_MAIN_KEYBOARD)
    return ADMIN_LOGGED_IN

def member_logged_in(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is the main entry for members.'''
    text = update.message.text
    token = context.chat_data['token']
    # Navigate to timeline section
    if text == 'Timeline':
        response, status = get_with_auth(ApiUrls.MEMBER_CATEGORY_ROOT.value, token)
        
        # Create message
        message = 'List of all course sections:\n\n'
        for i, cat in enumerate(response):
            message += f"{i+1}) {cat['title']} {'✅' if cat['is_taught'] else '❌'}\n\n"
        
        update.message.reply_text(text=message, reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN

    # Navigate to resources section
    elif text == 'Resources':
        response, status = get_with_auth(ApiUrls.MEMBER_CATEGORY_ROOT.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        
        # Creating buttons using retrieved categories and store cateegory id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='ُThis service not available right now!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        
        keyboard_buttons = []
        context.chat_data['categories'] = dict()
        for i,cat in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {cat['title']}")
            context.chat_data['categories'][f"{i+1}) {cat['title']}"] = cat['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please select a category!', reply_markup=keyboard)
        
        context.chat_data['action'] = 'res'
        return MEMBER_GET_CATEGORIES

    elif text == 'Questions':
        update.message.reply_text(text='You are in questions section.', reply_markup=MEMBER_QUESTIONS_KEYBOARD)
        return MEMBER_QUESTIONS_MAIN

    # Navigate to homeworks or grades
    elif text == 'Homeworks' or text == 'Grades':
        # Sending request to get all available homeworks
        response, status = get_with_auth(ApiUrls.MEMBER_HOMEWORK_ROOT.value, token)
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='No homework available!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        
        keyboard_buttons = []
        context.chat_data['homeworks'] = dict()
        for i,hw in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {hw['title']}")
            context.chat_data['homeworks'][f"{i+1}) {hw['title']}"] = hw['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please choose the homework you want.', reply_markup=keyboard)
        return MEMBER_GET_HOMEWORKS if text == 'Homeworks' else MEMBER_GET_HOMEWORKS_GRADE

    # Logout user
    elif text == 'Logout':
        token = context.chat_data['token']
        chat_id = update.effective_chat.id
        response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        del context.chat_data['token']
        update.message.reply_text(text='You logged out successfully!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

def register_admin(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is a secret command for registering admins.'''
    update.message.reply_text(text='We are in admin register section. You can use /cancel to cancel the operation in each section.\n Now, Please enter your email!')
    return REGISTER_ADMIN_ENTER_EMAIL

def register_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Check if the email is AUT email
    if re.fullmatch(AUT_EMAIL_REGEX, update.message.text):
        context.chat_data['email'] = update.message.text #Saving the email to use it in next request
        #Send the otp
        update.message.reply_text(text='Please wait...')
        response, status = post(ApiUrls.SEND_OTP.value, email=update.message.text)
        if status == 200:
            update.message.reply_text(text=f'Otp sent to {update.message.text}. Please enter the otp:', reply_markup=CANCEL_KEYBOARD)
            return REGISTER_ENTER_OTP
        update.message.reply_text(text=response['detail'], reply_markup=CANCEL_KEYBOARD)
        return REGISTER_ENTER_EMAIL
    update.message.reply_text(text='This is not an AUT email dude! Please re enter your email!', reply_markup=CANCEL_KEYBOARD)
    return REGISTER_ENTER_EMAIL

def register_enter_otp(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Check if the otp is valid
    if re.fullmatch(OTP_REGEX, update.message.text):
        email = context.chat_data['email']
        #Check the otp correctness given the email and otp
        response, status = post(ApiUrls.ACTIVATE_ACCOUNT.value, email=email, otp=update.message.text)
        if status == 200:
            update.message.reply_text(text='Register completed!', reply_markup=CANCEL_KEYBOARD)
            return NOT_LOGGED_IN
        update.message.reply_text(text=response['detail'], reply_markup=CANCEL_KEYBOARD)
        return REGISTER_ENTER_OTP
    update.message.reply_text(text='The OTP format is not correct. it must be a 5 digit number.', reply_markup=CANCEL_KEYBOARD)
    return REGISTER_ENTER_OTP

def login_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Checking if the email is valid
    if re.fullmatch(SIMPLE_EMAIL_REGEX, update.message.text):
        context.chat_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter your student id.', reply_markup=CANCEL_KEYBOARD)
        return LOGIN_ENTER_PASSWORD
    update.message.reply_text(text='This is not an email dude! Please re enter your email!', reply_markup=CANCEL_KEYBOARD)
    return LOGIN_ENTER_EMAIL

def login_enter_password(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Send the login request
    email = context.chat_data['email']
    response, status = post(ApiUrls.LOGIN.value, username=email, password=update.message.text, chat_id=update.effective_chat.id)
    if status == 200:
        # Fill local storage data to authorize user at next requests
        context.chat_data['token'] = response['token']
        context.chat_data['is_admin'] = response['is_admin']
        # Navigate to admin panel if the user is admin
        if response['is_admin']:
            if 'questions' not in context.chat_data.keys():
                context.chat_data['questions'] = dict()
            update.message.reply_text(text='Logged in successfully as admin!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        # Navigate to member panel if the user is not admin
        update.message.reply_text(text='Logged in successfully!', reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN
    # Try again if the credentials are not correct
    update.message.reply_text(text='email or password is not correct. Please enter your email again!', reply_markup=CANCEL_KEYBOARD)
    return LOGIN_ENTER_EMAIL
        
def register_admin_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Check if the entered email is literally an email
    if re.fullmatch(SIMPLE_EMAIL_REGEX, update.message.text):
        context.chat_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter the secret :)', reply_markup=CANCEL_KEYBOARD)
        return REGISTER_ADMIN_ENTER_SECRET
    # Try again if the email is not valid
    update.message.reply_text(text='This is not an email dude! Please re enter your email!', reply_markup=CANCEL_KEYBOARD)
    return REGISTER_ADMIN_ENTER_EMAIL

def register_admin_enter_secret(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Send the register request
    email = context.chat_data['email']
    response, status = post(ApiUrls.REGISTER_ADMIN.value, email=email, secret=update.message.text)
    if status == 200:
        update.message.reply_text(text='Admin access activated!', reply_markup=CANCEL_KEYBOARD)    
        return NOT_LOGGED_IN
    # Try again if the secret key is not correct
    update.message.reply_text(text='The secret is not correct. Please enter the secret again!', reply_markup=CANCEL_KEYBOARD)
    return REGISTER_ADMIN_ENTER_SECRET

def admin_homeworks_main(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is the main entry for admin homeworks.'''
    text = update.message.text
    # Navigate to manage homeworks section
    if text == 'Manage Current Homeworks':
        token = context.chat_data['token']
        # Sending request to get all available homeworks
        response, status = get_with_auth(ApiUrls.ADMIN_HOMEWORK_ROOT.value, token)
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='No homework available!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
        
        keyboard_buttons = []
        context.chat_data['homeworks'] = dict()
        for i,hw in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {hw['title']}")
            context.chat_data['homeworks'][f"{i+1}) {hw['title']}"] = hw['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please choose the homework you want.', reply_markup=keyboard)
        return ADMIN_MANAGE_HOMEWORKS
        
    elif text == 'Create a New Homework':
        context.chat_data['homework_input'] = dict()
        context.chat_data['action'] = 'create'
        update.message.reply_text(text='Please enter the title of the homework!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_TITLE
    
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
    return ADMIN_HOMEWORKS_MAIN

def admin_manage_homeworks(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    homeworks = context.chat_data['homeworks']
    # Save selected hw id in local storage to use it later in requests.
    if text in homeworks.keys():
        context.chat_data['selected_hw_id'] = homeworks[text]
        update.message.reply_text(f'What do you want to do with this homework?', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_MANAGE_HOMEWORKS

def admin_each_homework(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is an entry for working with an invidual homework.'''
    text = update.message.text
    selected_hw_id = context.chat_data['selected_hw_id']
    token = context.chat_data['token']
    # Retrieve home work details
    if text == 'Homework Details':
        response, status = get_with_auth(f'{ApiUrls.ADMIN_HOMEWORK_ROOT.value}{selected_hw_id}/', token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        # Creating message
        link =  f"[link]({response['grade_link']})" if response['grade_link'] else 'No link attached.'
        message = f"Details of {response['title']}:\n\n \
                    Deadline: {timestamp_to_jalali(response['due_date_time'])} \n\n \
                    The homework {'is' if response['published'] else 'is not'} published. \n\n \
                    Grades: {link} \n\n \
                    Homework file {'is' if response['file'] is not None else 'is not'} attached."
        # Getting hw file if needed
        if response['file'] is not None:
            update.message.reply_text(text=message, parse_mode='Markdown', disable_web_page_preview=True)
            update.message.reply_text(f'Uploading the HW file...', reply_markup=ADMIN_EACH_HW_KEYBOARD)
            file_address = get_file(response['file'])
            with open(file_address, 'rb') as file:
                bot.send_document(chat_id=update.effective_chat.id, document=file)
        else:
            update.message.reply_text(text=message, reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Send publish request
    elif text == 'Publish HW':
        response,status = patch_with_auth(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=selected_hw_id), token, published=True)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text=f'The homework is now published!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Send unpublish request
    elif text == 'Unpublish HW':
        response,status = patch_with_auth(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=selected_hw_id), token, published=False)
        #TODO: handle 500 errors
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text=f'The homework is now unpublished!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Send grade publish request
    elif text == 'Publish Grades':
        response,status = post_with_auth(ApiUrls.ADMIN_HOMEWORK_GRADE_PUBLISH.value.format(id=selected_hw_id), token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text=f'The grades are now published!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Send grade unpublish request
    elif text == 'Unpublish Grades':
        response,status = post_with_auth(ApiUrls.ADMIN_HOMEWORK_GRADE_UNPUBLISH.value.format(id=selected_hw_id), token)
        #TODO: handle 500 errors
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text=f'The grades are now unpublished!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Navigate to confirmation page to delete
    elif text == 'Delete HW':
        context.chat_data['confirmation_action'] = 'HW_DELETE'
        update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
        return ADMIN_CONFIRMATION_STATE
    # Navigate to update Grade
    elif text == 'Update HW Grades':
        update.message.reply_text(text='Please enter the link of the grades.', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_UPDATE_GRADE_ENTER_LINK
    # Navigate to hw select title
    elif text == 'Update HW':
        context.chat_data['homework_input'] = dict()
        context.chat_data['action'] = 'update'
        update.message.reply_text(text='Please enter the title of the homework or use skip button to keep the previous value.', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_TITLE
    #TODO: add other commands here 
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
    return ADMIN_EACH_HOMEWORK

def admin_confirmation_state(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    confirmation_action = context.chat_data['confirmation_action']
    # Delete if confirmed
    if text == CONFIRM_KEYWORD:
        token = context.chat_data['token']
        # DELETE HW
        if confirmation_action == 'HW_DELETE':
            id_to_delete = context.chat_data['selected_hw_id']
            response,status = delete_with_auth(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=id_to_delete), token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
                return ADMIN_EACH_HOMEWORK
            update.message.reply_text(text='Homework deleted successfully!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
        # DELETE RESOURCE
        elif confirmation_action == 'RES_DELETE':
            id_to_delete = context.chat_data['selected_res_id']
            response,status = delete_with_auth(ApiUrls.ADMIN_RESOURCES_WITH_ID.value.format(id=id_to_delete), token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
                return ADMIN_EACH_RESOURCE
            update.message.reply_text(text='Resource deleted successfully!', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY
        # SEND NOTIF
        elif confirmation_action == 'SEND_NOTIF':
            text = context.chat_data['notif_text']
            token = context.bot_data['token']
            response,status = get_with_auth(ApiUrls.ALL_STUDENTS_SESSIONS.value, token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
                return ADMIN_EACH_RESOURCE
            sent = 0
            failed = 0
            failed_list = []
            for chat_id in response:
                try:
                    context.bot.send_message(chat_id, text=f"New Notification:\n\n{text}")
                    sent += 1
                except:
                    failed += 1
                    failed_list.append(chat_id)
            
            if failed == 0:
                update.message.reply_text(text='Notif was sent successfuly!', reply_markup=ADMIN_MAIN_KEYBOARD)
            else:
                text = f"Notif was sent to {sent}/{sent + failed} students successfully!\n\nFailed users:\n"
                for i,chat_id in enumerate(failed_list):
                    text += f"[user{i+1}](tg://user?id={chat_id}"
                update.message.reply_text(text=text, reply_markup=ADMIN_MAIN_KEYBOARD, parse_mode='Markdown')
            return ADMIN_LOGGED_IN

    elif text == DECLINE_KEYWORD:
        if confirmation_action == 'HW_DELETE':
            update.message.reply_text(text='Operation canceled!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        elif confirmation_action == 'RES_DELETE':
            update.message.reply_text(text='Operation canceled!', reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
            return ADMIN_EACH_RESOURCE
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=CONFIRMATION_KEYBOARD)
    return ADMIN_CONFIRMATION_STATE

def admin_update_grade_enter_link(update: telegram.Update, context: telegram.ext.CallbackContext):
    link = update.message.text
    # Check if the url is valid
    if re.fullmatch(URL_REGEX, link):
        selected_hw_id = context.chat_data['selected_hw_id']
        token = context.chat_data['token']
        response, status = put_with_auth(ApiUrls.ADMIN_HOMEWORK_GRADE.value.format(id=selected_hw_id), token, link=link, published=False)
        print(response)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text='Grades updated successfully!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Please enter a valid url!', reply_markup=CANCEL_KEYBOARD)
    return ADMIN_UPDATE_GRADE_ENTER_LINK

def admin_homeworks_title(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.chat_data['action']
    # if the action is 'create' we must get the entered text. if the action is 'update' we must get the entered text unless it is 'skip'.
    if (action == 'update' and text != SKIP_KEYWORD) or (action == 'create'):
        context.chat_data['homework_input']['title'] = text

    if action == 'update':
        update.message.reply_text('Now, please send the homework file or skip to keep the previous file.', reply_markup=SKIP_CANCEL_KEYBOARD)
    elif action == 'create':
        update.message.reply_text('Now, please send the homework file or skip and update the file later.', reply_markup=SKIP_CANCEL_KEYBOARD)
    return ADMIN_HOMEWORKS_FILE

def admin_homeworks_file(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    # If a file is sent we must download it.
    if text is None:
        file = context.bot.get_file(update.message.document)
        file_name = get_file_name(file.file_path)
        file.download(f'./downloads/{file_name}')
        context.chat_data['homework_input']['file'] = f'./downloads/{file_name}'
    # If user enters shit
    elif text != SKIP_KEYWORD:
        update.message.reply_text('please send the homework file or skip!', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_FILE

    action = context.chat_data['action']
    if action == 'update':
        update.message.reply_text('Now, please set the homework due date or skip to keep the previous deadline.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=SKIP_CANCEL_KEYBOARD)
    elif action == 'create':
        update.message.reply_text('Now, please set the homework due date.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=CANCEL_KEYBOARD)
    return ADMIN_HOMEWORKS_DUE_DATE

def admin_homeworks_due_date(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.chat_data['action']
    #if the date time is valid we must convert it to gregorian date time
    if is_valid_date_time(text):
        context.chat_data['homework_input']['due_date_time'] = jalali_to_gregorian(text)
    # if user enters shit
    elif action == 'create':
        update.message.reply_text('Please enter a valid date time.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE
    elif action == 'update' and text != SKIP_KEYWORD:
        update.message.reply_text('Now, please set the homework due date or skip to keep the previous deadline.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE

    token = context.chat_data['token']
    data = context.chat_data['homework_input']
    # Send update request if action is update
    if action == 'update':
        selected_hw_id = context.chat_data['selected_hw_id']
        response, status = multipart_form_data(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=selected_hw_id), token, data, file_address=data.get('file',None), method='PATCH')
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
            return ADMIN_EACH_HOMEWORK
        update.message.reply_text(text='Homework updated successfully!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK
    # Send post request if action is create
    elif action == 'create':
        body = dict()
        body['title'] = data['title']
        body['due_date_time'] = data['due_date_time']
        file_address = data.get('file',None)
        response, status = multipart_form_data(ApiUrls.ADMIN_HOMEWORK_ROOT.value, token, body, file_address=file_address, method='POST')
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
        update.message.reply_text(text='Homework created successfully!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
        return ADMIN_HOMEWORKS_MAIN

def admin_get_categories(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    categories = context.chat_data['categories']
    # Save selected category id in local storage to use it later in requests.
    if text[:-2] in categories.keys():
        context.chat_data['selected_cat_id'] = categories[text[:-2]]
        update.message.reply_text(f'What do you want to do with this category?', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_CATEGORIES

def admin_each_category(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.chat_data['token']
    # Change status of the category for timeline
    if text == 'Change Status':
        selected_cat_id = context.chat_data['selected_cat_id']
        response, status = put_with_auth(ApiUrls.ADMIN_CATEGORY_TOGGLE_STATUS.value.format(id=selected_cat_id), token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY
        update.message.reply_text(text=f"Category status changed to {'✅' if response['is_taught'] else '❌'}", reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY
    # Manage current resources of the category
    elif text == 'Manage Current Resources':
        selected_cat_id = context.chat_data['selected_cat_id']
        response, status = get_with_auth(ApiUrls.ADMIN_CATEGORY_RESOURCES.value.format(id=selected_cat_id), token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='Timeline not available!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        keyboard_buttons = []
        context.chat_data['resources'] = dict()
        for i,res in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {res['title']}")
            context.chat_data['resources'][f"{i+1}) {res['title']}"] = res['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Which resource do you want to change??', reply_markup=keyboard)
        return ADMIN_GET_RESOURCES
    # Add a new Resource
    elif text == 'Add a New Resource':
        context.chat_data['resource_input'] = dict()
        context.chat_data['action'] = 'create'
        update.message.reply_text(text='Please enter the resource title!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_RESOURCE_TITLE

    # Get all unanswered questions related
    elif text == 'Get All Unanswered Questions':
        response, status = get_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_ROOT.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        chat_id = update.effective_chat.id
        for question in response:
            message_text = f"Question from [user](tg://user?id={update.effective_user.id}):\n\n{question['question']})"
            message = context.bot.send_message(chat_id, message_text, parse_mode='Markdown')
            response, status = put_with_auth_and_body(ApiUrls.ADMIN_QUESTION_ANSWER_WITH_ID.value.format(id=question['id']), token, [{"chat_id":chat_id,"message_id":message.message_id}])
            context.chat_data['questions'][str(message.message_id)] = question['id']
            if status != 200:
                update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
                return ADMIN_LOGGED_IN
        update.message.reply_text(text='All questions are sent!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN

    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_EACH_CATEGORY

def admin_get_resources(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    resources = context.chat_data['resources']
    # Save selected resource id in local storage to use it later in requests.
    if text in resources.keys():
        context.chat_data['selected_res_id'] = resources[text]
        update.message.reply_text(f'What do you want to do with this resource?', reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
        return ADMIN_EACH_RESOURCE

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_RESOURCES

def admin_each_resource(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.chat_data['token']
    selected_res_id = context.chat_data['selected_res_id']
    # Show details of an individiual resource
    if text == 'Get Resource Details':
        response, status = get_with_auth(ApiUrls.ADMIN_RESOURCES_WITH_ID.value.format(id=selected_res_id), token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        update.message.reply_text(f"Resource name: {response['title']}\n\nResource link: [link]({response['link']})", reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD,parse_mode='Markdown')
        return ADMIN_EACH_RESOURCE
    
    # Navigate to confirmation section to delete
    elif text == 'Delete Resource':
        context.chat_data['confirmation_action'] = 'RES_DELETE'
        update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
        return ADMIN_CONFIRMATION_STATE
    # Navigate to update section
    elif text == 'Update Resource':
        context.chat_data['resource_input'] = dict()
        context.chat_data['action'] = 'update'
        update.message.reply_text(text='Please enter the resource title or use skip to keep the previous value.', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_RESOURCE_TITLE
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_RESOURCES

def admin_resource_title(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.chat_data['action']
    # if the action is 'create' we must get the entered text. if the action is 'update' we must get the entered text unless it is 'skip'.
    if (action == 'update' and text != SKIP_KEYWORD) or (action == 'create'):
        context.chat_data['resource_input']['title'] = text

    if action == 'update':
        update.message.reply_text('Now, please send the resource link or skip to keep the previous link.', reply_markup=SKIP_CANCEL_KEYBOARD)
    elif action == 'create':
        update.message.reply_text('Now, please send the resource link.', reply_markup=CANCEL_KEYBOARD)
    return ADMIN_RESOURCE_LINK

def admin_resource_link(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.chat_data['action']
    #if the date time is valid we must convert it to gregorian date time
    if re.fullmatch(URL_REGEX, text):
        context.chat_data['resource_input']['link'] = text
    # if user enters shit
    elif action == 'create': 
        update.message.reply_text('Please enter a valid URL!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE
    elif action == 'update' and text != SKIP_KEYWORD:
        update.message.reply_text('Please enter a valid URL or skip to keep the previous link!', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE

    token = context.chat_data['token']
    data = context.chat_data['resource_input']
    # Send update request if action is update
    if action == 'update':
        patch_data = dict()
        for key,value in data.items():
            if value is not None:
                patch_data[key] = value

        selected_res_id = context.chat_data['selected_res_id']
        response, status = patch_with_auth_and_body(ApiUrls.ADMIN_RESOURCES_WITH_ID.value.format(id=selected_res_id), token, patch_data)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
            return ADMIN_EACH_RESOURCE
        update.message.reply_text(text='Resource updated successfully!', reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
        return ADMIN_EACH_RESOURCE
    # Send post request if action is create
    elif action == 'create':
        selected_cat_id = context.chat_data['selected_cat_id']
        response, status = post_with_auth(ApiUrls.ADMIN_CATEGORY_RESOURCES.value.format(id=selected_cat_id), token, title=data['title'], link=data['link'])
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY
        update.message.reply_text(text='Resource created successfully!', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY


def admin_send_notif(update: telegram.Update, context: telegram.ext.CallbackContext):
    context.chat_data['notif_text'] = update.message.text
    context.chat_data['confirmation_action'] = 'SEND_NOTIF'
    update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
    return ADMIN_CONFIRMATION_STATE


def admin_incoming_notifs(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.chat_data['token']
    # Enable notifs
    if text == ENABLE_KEYWORD:
        response,status = post_with_auth(ApiUrls.ADMIN_INCOMING_NOTIF_ENABLE.value, token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        update.message.reply_text(text='Incoming notifs enabled!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    # Disable notifs
    elif text == DISABLE_KEYWORD:
        response,status = post_with_auth(ApiUrls.ADMIN_INCOMING_NOTIF_DISABLE.value, token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        update.message.reply_text(text='Incoming notifs disabled!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_RESOURCES
    
def member_get_categories(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    categories = context.chat_data['categories']
    action = context.chat_data['action']
    # Save selected category id in local storage to use it later in requests.
    if action == 'res':
        if text in categories.keys():
            selected_cat_id = categories[text]
            token = context.chat_data['token']
            
            # Find resources
            response, status = get_with_auth(ApiUrls.MEMBER_CATEGORY_RESOURCES.value.format(id=selected_cat_id), token)
            if status != 200:
                update.message.reply_text(text='Oops! Something went wrong!', reply_markup=MEMBER_MAIN_KEYBOARD)
                return MEMBER_LOGGED_IN
            
            if len(response) == 0:
                update.message.reply_text(text='There is no resource available.', reply_markup=MEMBER_MAIN_KEYBOARD)
                return MEMBER_LOGGED_IN

            message = 'List of resources:\n\n'
            for i, res in enumerate(response):
                message += f'{i+1}) ({res.title})[{res.link}]\n'

            update.message.reply_text(text=message, reply_markup=MEMBER_MAIN_KEYBOARD, parse_mode='Markdown')
            return MEMBER_LOGGED_IN

    elif action == 'ask':
        if text in categories.keys():
            selected_cat_id = categories[text]
            context.chat_data['selected_cat_id'] = selected_cat_id
            token = context.chat_data['token']
            update.message.reply_text(text='Please send me your question.', reply_markup=CANCEL_KEYBOARD)
            return MEMBER_ASK_QUESTION

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

def member_get_homeworks(update: telegram.Update, context: telegram.ext.CallbackContext):
    token = context.chat_data['token']
    text = update.message.text
    homeworks = context.chat_data['homeworks']
    # Save selected hw id in local storage to use it later in requests.
    if text in homeworks.keys():
        selected_hw_id = homeworks[text]
        response, status = get_with_auth(ApiUrls.MEMBER_HOMEWORK_WITH_ID.value.format(id=selected_hw_id), token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        # Creating message
        message = f"Details of {response['title']}:\n\n \
                    Deadline: {timestamp_to_jalali(response['due_date_time'])} \n\n \
                    Homework file {'is' if response['file'] is not None else 'is not'} attached."
        # Getting hw file if needed
        if response['file'] is not None:
            update.message.reply_text(text=message, parse_mode='Markdown', disable_web_page_preview=True)
            update.message.reply_text(f'Uploading the HW file...', reply_markup=MEMBER_MAIN_KEYBOARD)
            file_address = get_file(response['file'])
            with open(file_address, 'rb') as file:
                bot.send_document(chat_id=update.effective_chat.id, document=file)
        else:
            update.message.reply_text(text=message, reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

def member_get_homeworks_grade(update: telegram.Update, context: telegram.ext.CallbackContext):
    token = context.chat_data['token']
    text = update.message.text
    homeworks = context.chat_data['homeworks']
    # Save selected hw id in local storage to use it later in requests.
    if text in homeworks.keys():
        selected_hw_id = homeworks[text]    
        response, status = get_with_auth(ApiUrls.MEMBER_HOMEWORK_GRADES.value.format(id=selected_hw_id), token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        # Creating message
        message = f"Here is the [link]({response['link']}) of grades."
        update.message.reply_text(text=message, reply_markup=MEMBER_MAIN_KEYBOARD, parse_mode='Markdown')
        return MEMBER_LOGGED_IN
    
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

def member_questions_main(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.chat_data['token']

    if text == 'Ask a Question':
        response, status = get_with_auth(ApiUrls.MEMBER_CATEGORY_ROOT.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        
        # Creating buttons using retrieved categories and store cateegory id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='ُThis service not available right now!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_LOGGED_IN
        
        keyboard_buttons = []
        context.chat_data['categories'] = dict()
        for i,cat in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {cat['title']}")
            context.chat_data['categories'][f"{i+1}) {cat['title']}"] = cat['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please select a category!', reply_markup=keyboard)
        
        context.chat_data['action'] = 'ask'
        return MEMBER_GET_CATEGORIES

    elif text == 'My Questions':
        response, status = get_with_auth(ApiUrls.MEMBER_MY_QUEESTIONS.value, token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_QUESTIONS_MAIN

        # Creating buttons using retrieved categories and store cateegory id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='ُYou have not asked any question yet!', reply_markup=MEMBER_MAIN_KEYBOARD)
            return MEMBER_QUESTIONS_MAIN
        
        keyboard_buttons = []
        context.chat_data['my_questions'] = dict()
        for i,q in enumerate(response):
            text = f"{i+1}) {q['question']} {'✅' if  q['answer']!='' else '❌'}"
            keyboard_buttons.append(text)
            context.chat_data['my_questions'][text] = q['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please select a question!', reply_markup=keyboard)
        
        context.chat_data['action'] = 'res'
        return MEMBER_MY_QUESTIONS

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_QUESTIONS_MAIN

def member_my_questions(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    selected_question_id = context.chat_data['my_questions'].get(text, None)
    if selected_question_id is not None:
        token = context.chat_data['token']
        response, status = get_with_auth(ApiUrls.MEMBER_QUESTION_ANSWER_WITH_ID.value.format(id=selected_question_id), token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=MEMBER_QUESTIONS_KEYBOARD)
            return MEMBER_QUESTIONS_MAIN
        
        message = f"Question:\n{response['question']}\n\nAnswer:\n{response['answer'] if response['answer'] is not None else 'No answer yet!'}"
        update.message.reply_text(text=message, reply_markup=MEMBER_QUESTIONS_KEYBOARD)
        return MEMBER_QUESTIONS_MAIN
    
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=MEMBER_QUESTIONS_KEYBOARD)
    return MEMBER_QUESTIONS_MAIN

def member_ask_question(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.chat_data['token']
    bot_token = context.bot_data['token']
    selected_cat_id = context.chat_data['selected_cat_id']

    # Create Question
    response, status = post_with_auth(ApiUrls.MEMBER_CATEGORY_ADD_QUESTION.value.format(id=selected_cat_id), token, question=text, chat_id=update.effective_chat.id)
    if status != 200:
        update.message.reply_text(text='Operation failed!', reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN
    
    question_id = response['id']
    # Get All admins who allowed_notif
    
    response, status = get_with_auth(ApiUrls.ADMIN_INCOMING_NOTIF_ADMINS.value, bot_token)
    if status != 200:
        # TODO: add log here
        return MEMBER_LOGGED_IN
    
    message_text = f'A new question from [user](tg://user?id={update.effective_user.id}):\n\n{text}'
    message_data = []

    if context.bot_data.get('questions_data', None) is None: 
        context.bot_data['questions_data'] = dict()

    for chat_id in response:
        try:
            if context.bot_data['questions_data'].get(chat_id, None) is None: 
                context.bot_data['questions_data'][chat_id]= dict()
            message = context.bot.send_message(chat_id, message_text, parse_mode='Markdown')
            context.bot_data['questions_data'][chat_id][str(message.message_id)] = question_id
            print(message.message_id)
            data = {'chat_id': chat_id, 'message_id': message.message_id}
            message_data.append(data)
        except Exception as e:
            print(e)
            pass
    # Save question
    response, status = put_with_auth_and_body(ApiUrls.ADMIN_QUESTION_ANSWER_WITH_ID.value.format(id=question_id), bot_token, message_data)
    if status != 200:
        # TODO: add log here
        return MEMBER_LOGGED_IN

    print('done')
    update.message.reply_text(text='Question sent! I will forward the answer to you as soon as possible!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN
    
def admin_questions(update: telegram.Update, context: telegram.ext.CallbackContext):
    token = context.chat_data['token']
    response,status = None,None
    answered = update.message.text == 'Get All Answered Questions'
    response, status = get_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_ROOT.value, token, answered=answered)

    # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
    if len(response) == 0:
        update.message.reply_text(text='There is no question!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    
    keyboard_buttons = []
    context.chat_data['questions'] = dict()
    for i,res in enumerate(response):
        keyboard_buttons.append(f"{res['question']}")
        context.chat_data['questions'][f"{res['question']}"] = res['id']

    update.message.reply_text(text="You can choose one question and reply that by /answer.", reply_markup=create_vertical_keyboard_with_cancel_button(keyboard_buttons))
    return ADMIN_EACH_QUESTION

def admin_each_question(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    selected_question_id = context.chat_data['questions'].get(text, None)
    if selected_question_id is None:
        update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_QUESTIONS_KEYBOARD)
        return ADMIN_QUESTIONS
    
    token = context.chat_data['token']
    response,status = get_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_WITH_ID.value.format(id=selected_question_id), token)
    if status != 200:
        update.message.reply_text(text='Oops! sth went wrong.', reply_markup=ADMIN_QUESTIONS_KEYBOARD)
        return ADMIN_QUESTIONS
    
    message_text = f"From [user](tg://user?id={update.effective_user.id}):\n\nQuestion:\n{response['question']}"
    if response['answer'] is not None:
        message_text += f"\n\nAnswer:\n{response['answer']}"

    message = update.message.reply_text(text=message_text, parse_mode='Markdown')
    chat_id = update.effective_chat.id
    response, status = put_with_auth_and_body(ApiUrls.ADMIN_QUESTION_ANSWER_WITH_ID.value.format(id=selected_question_id), token, [{'chat_id': str(chat_id), 'message_id': message.message_id}])
    if status != 200:
        update.message.reply_text(text='Oops! sth went wrong.', reply_markup=ADMIN_QUESTIONS_KEYBOARD)
        return ADMIN_QUESTIONS
    
    update.message.reply_text(text='Back to the questions section!', reply_markup=ADMIN_QUESTIONS_KEYBOARD)
    return ADMIN_QUESTIONS

@get_last_login
def answer(update: telegram.Update, context: telegram.ext.CallbackContext):
    if not context.chat_data['is_admin']:
        update.message.reply_text(text='Sorry I didnt understand', reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN
        
    question_message = update.message.reply_to_message
    chat_id = update.effective_chat.id
    question_id = context.bot_data['questions_data'][chat_id][str(question_message.message_id)]
    answer = update.message.text[len('/answer '):]

    token = context.chat_data['token']
    response, status = put_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_ANSWER.value.format(id=question_id), token, answer=answer)
    if status != 200:
        update.message.reply_text(text=response['detail'], reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    
    sessions_response, status = get_with_auth(ApiUrls.ACTIVE_SESSIONS.value, token, user_id=response['user'])
    if status != 200:
        update.message.reply_text(text='Failed to forward the answer to user!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN
    
    successful = []
    for chat_id in sessions_response:
        message = f"New answer for your question!\n\nQuestion: {response['question']}\n\nAnswer: {answer}"
        successful.append(chat_id)
        try:
            context.bot.send_message(chat_id, message)
        except:
            update.message.reply_text(text=f'Failed to forward the answer to [account](tg://user?id={chat_id})', reply_markup=ADMIN_MAIN_KEYBOARD, parse_mode='Markdown')
    
    message = "The answer successfully sent to account(s):\n"
    for i,chat_id in enumerate(successful):
        message += f"[account{i+1}](tg://user?id={chat_id})"

    update.message.reply_text(message, reply_markup=ADMIN_MAIN_KEYBOARD, parse_mode='Markdown')
    return ADMIN_LOGGED_IN
    
conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler((Filters.text & ~ Filters.command), entry_message_handler), MessageHandler(Filters.command & Filters.regex('/cancel'), cancel)],
        states={
            # NOT_LOGGED_IN STATE
            NOT_LOGGED_IN: [MessageHandler((Filters.text & ~ Filters.command), not_logged_in)],

            # LOGGED IN STATES
            MEMBER_LOGGED_IN: [MessageHandler((Filters.text & ~ Filters.command), member_logged_in)],
            ADMIN_LOGGED_IN: [MessageHandler((Filters.text & ~ Filters.command), admin_logged_in)],

            # REGISTER STATES
            REGISTER_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), register_enter_email)],
            REGISTER_ENTER_OTP: [MessageHandler((Filters.text & ~ Filters.command), register_enter_otp)],
            
            # LOGIN STATES
            LOGIN_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), login_enter_email)],
            LOGIN_ENTER_PASSWORD: [MessageHandler((Filters.text & ~ Filters.command), login_enter_password)],

            # REGISTER_ADMIN STATES
            REGISTER_ADMIN_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_email)],
            REGISTER_ADMIN_ENTER_SECRET: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_secret)],

            # ADMIN_HOMEWORK
            ADMIN_HOMEWORKS_MAIN: [MessageHandler((Filters.text & ~ Filters.command), admin_homeworks_main)],
            ADMIN_MANAGE_HOMEWORKS: [MessageHandler((Filters.text & ~ Filters.command), admin_manage_homeworks)],
            ADMIN_EACH_HOMEWORK: [MessageHandler((Filters.text & ~ Filters.command), admin_each_homework)],
            ADMIN_HOMEWORKS_TITLE: [MessageHandler((Filters.text & ~ Filters.command), admin_homeworks_title)],
            ADMIN_HOMEWORKS_FILE: [MessageHandler(((Filters.document | Filters.text) & ~ Filters.command), admin_homeworks_file)],
            ADMIN_HOMEWORKS_DUE_DATE: [MessageHandler((Filters.text & ~ Filters.command), admin_homeworks_due_date)],
            ADMIN_UPDATE_GRADE_ENTER_LINK: [MessageHandler((Filters.text & ~ Filters.command), admin_update_grade_enter_link)],

            # ADMIN_TIMELINE & RESOURCES
            ADMIN_GET_CATEGORIES: [MessageHandler((Filters.text & ~ Filters.command), admin_get_categories)],
            ADMIN_EACH_CATEGORY: [MessageHandler((Filters.text & ~ Filters.command), admin_each_category)],

            ADMIN_GET_RESOURCES: [MessageHandler((Filters.text & ~ Filters.command), admin_get_resources)],
            ADMIN_EACH_RESOURCE: [MessageHandler((Filters.text & ~ Filters.command), admin_each_resource)],
            ADMIN_RESOURCE_TITLE: [MessageHandler((Filters.text & ~ Filters.command), admin_resource_title)],
            ADMIN_RESOURCE_LINK: [MessageHandler((Filters.text & ~ Filters.command), admin_resource_link)],

            # ADMIN NOTIFS
            ADMIN_INCOMIG_NOTIFS: [MessageHandler((Filters.text & ~ Filters.command), admin_incoming_notifs)],
            ADMIN_SEND_NOTIF: [MessageHandler((Filters.text & ~ Filters.command), admin_send_notif)],
            
            # ADMIN QUESTIONs
            ADMIN_QUESTIONS: [MessageHandler((Filters.text & ~ Filters.command), admin_questions)],
            ADMIN_EACH_QUESTION: [MessageHandler((Filters.text & ~ Filters.command), admin_each_question)],

            # MEMBER CATEGORIES
            MEMBER_GET_CATEGORIES: [MessageHandler((Filters.text & ~ Filters.command), member_get_categories)],

            # MEMBER HOMEWORKS
            MEMBER_GET_HOMEWORKS: [MessageHandler((Filters.text & ~ Filters.command), member_get_homeworks)],
            MEMBER_GET_HOMEWORKS_GRADE: [MessageHandler((Filters.text & ~ Filters.command), member_get_homeworks_grade)],
            
            # MEMBER QUESTIONS
            MEMBER_QUESTIONS_MAIN: [MessageHandler((Filters.text & ~ Filters.command), member_questions_main)],
            MEMBER_ASK_QUESTION: [MessageHandler((Filters.text & ~ Filters.command), member_ask_question)],
            MEMBER_MY_QUESTIONS: [MessageHandler((Filters.text & ~ Filters.command), member_my_questions)],
            
            ADMIN_CONFIRMATION_STATE: [MessageHandler((Filters.text & ~ Filters.command), admin_confirmation_state)]
        },
        fallbacks=[MessageHandler(Filters.command & Filters.regex('/cancel'), cancel), MessageHandler(Filters.command & Filters.regex('/answer .+'), answer)],
        allow_reentry=False
    )

dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()     