from calendar import calendar
from os import stat_result
from django.http import response
import telegram
from telegram import replymarkup
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
ADMIN_INCOMIG_NOTIFS, \
ADMIN_CONFIRMATION_STATE, \
MEMBER_TIMELINE = range(25)

# REGEX
SIMPLE_EMAIL_REGEX = '^[^@\s]+@[^@\s]+\.[^@\s]+$'
AUT_EMAIL_REGEX = '^[A-Za-z0-9._%+-]+@aut\.ac\.ir'
OTP_REGEX = '^[0-9]{5}'
URL_REGEX = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Logout if needed
    token = context.user_data.get('token', None)
    if token: 
        chat_id = update.effective_chat.id
        response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
    
    # Clear data and start again
    context.user_data.clear()
    context.user_data['is_admin'] = False
    update.message.reply_text(text='Hi! Use buttons to work with me!', reply_markup=NOT_LOGGED_IN_KEYBOARD)

    return NOT_LOGGED_IN

@get_last_login
def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Checking if user has logged in or not
    if 'token' not in context.user_data.keys():
        update.message.reply_text(text='Operation Canceled!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN

    # Navigate to admin panel if the user is admin
    if context.user_data['is_admin']:
        update.message.reply_text(text='Operation Canceled!', reply_markup=ADMIN_MAIN_KEYBOARD)
        return ADMIN_LOGGED_IN

    # Navigate to user panel if the user is not admin
    update.message.reply_text(text='Operation Canceled!', reply_markup=MEMBER_MAIN_KEYBOARD)
    return MEMBER_LOGGED_IN

@get_last_login
def entry_message_handler(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This handler is for recovering user state after restarting the bot. it fills user token and navigates it to panel.'''
    token = context.user_data.get('token', None)
    # Checking if the user had logged in
    if token is None:
        update.message.reply_text(text='Please choose one of the following options.', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN

    # Navigate to admin panel if the user is admin
    if context.user_data['is_admin']:
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
    token = context.user_data['token']
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
            update.message.reply_text(text='Timeline is not available!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        keyboard_buttons = []
        context.user_data['categories'] = dict()
        for i,cat in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {cat['title']} {'✅' if cat['is_taught'] else '❌'}")
            context.user_data['categories'][f"{i+1}) {cat['title']}"] = cat['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='You are in timeline & resources section. which category do you want to change?', reply_markup=keyboard)
        return ADMIN_GET_CATEGORIES
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

        del context.user_data['token']
        update.message.reply_text(text='You logged out successfully!', reply_markup=NOT_LOGGED_IN_KEYBOARD)
        return NOT_LOGGED_IN
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_MAIN_KEYBOARD)
    return ADMIN_LOGGED_IN

def member_logged_in(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is the main entry for members.'''
    text = update.message.text
    token = context.user_data['token']
    # Navigate to timeline section
    if text == 'Timeline':
        response, status = get_with_auth(ApiUrls.MEMBER_GET_CATEGORIES.value, token)
        
        # Create message
        message = 'List of all course sections:\n\n'
        for i, category in enumerate(response):
            message += f"{i+1}) {category['title']} -> {'taught' if category['is_taught'] else 'not taught'}\n\n"
        
        update.message.reply_text(text=message, reply_markup=MEMBER_MAIN_KEYBOARD)
        return MEMBER_LOGGED_IN
    # Logout user
    elif text == 'Logout':
        token = context.user_data['token']
        chat_id = update.effective_chat.id
        response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        del context.user_data['token']
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
        context.user_data['email'] = update.message.text #Saving the email to use it in next request
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
        email = context.user_data['email']
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
        context.user_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter your student id.', reply_markup=CANCEL_KEYBOARD)
        return LOGIN_ENTER_PASSWORD
    update.message.reply_text(text='This is not an email dude! Please re enter your email!', reply_markup=CANCEL_KEYBOARD)
    return LOGIN_ENTER_EMAIL

def login_enter_password(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Send the login request
    email = context.user_data['email']
    response, status = post(ApiUrls.LOGIN.value, username=email, password=update.message.text, chat_id=update.effective_chat.id)
    if status == 200:
        # Fill local storage data to authorize user at next requests
        context.user_data['token'] = response['token']
        context.user_data['is_admin'] = response['is_admin']
        # Navigate to admin panel if the user is admin
        if response['is_admin']:
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
        context.user_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter the secret :)', reply_markup=CANCEL_KEYBOARD)
        return REGISTER_ADMIN_ENTER_SECRET
    # Try again if the email is not valid
    update.message.reply_text(text='This is not an email dude! Please re enter your email!', reply_markup=CANCEL_KEYBOARD)
    return REGISTER_ADMIN_ENTER_EMAIL

def register_admin_enter_secret(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Send the register request
    email = context.user_data['email']
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
        token = context.user_data['token']
        # Sending request to get all available homeworks
        response, status = get_with_auth(ApiUrls.ADMIN_HOMEWORK_ROOT.value, token)
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='No homework available!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
        
        keyboard_buttons = []
        context.user_data['homeworks'] = dict()
        for i,hw in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {hw['title']}")
            context.user_data['homeworks'][f"{i+1}) {hw['title']}"] = hw['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please choose the homework you want.', reply_markup=keyboard)
        return ADMIN_MANAGE_HOMEWORKS
        
    elif text == 'Create a New Homework':
        context.user_data['homework_input'] = dict()
        context.user_data['action'] = 'create'
        update.message.reply_text(text='Please enter the title of the homework!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_TITLE
    
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
    return ADMIN_HOMEWORKS_MAIN

def admin_manage_homeworks(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    homeworks = context.user_data['homeworks']
    # Save selected hw id in local storage to use it later in requests.
    if text in homeworks.keys():
        context.user_data['selected_hw_id'] = homeworks[text]
        update.message.reply_text(f'What do you want to do with this homework?', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_MANAGE_HOMEWORKS

def admin_each_homework(update: telegram.Update, context: telegram.ext.CallbackContext):
    '''This is an entry for working with an invidual homework.'''
    text = update.message.text
    selected_hw_id = context.user_data['selected_hw_id']
    token = context.user_data['token']
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
        context.user_data['confirmation_action'] = 'HW_DELETE'
        update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
        return ADMIN_CONFIRMATION_STATE
    # Navigate to update Grade
    elif text == 'Update HW Grades':
        update.message.reply_text(text='Please enter the link of the grades.', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_UPDATE_GRADE_ENTER_LINK
    # Navigate to hw select title
    elif text == 'Update HW':
        context.user_data['homework_input'] = dict()
        context.user_data['action'] = 'update'
        update.message.reply_text(text='Please enter the title of the homework or use skip button to keep the previous value.', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_TITLE
    #TODO: add other commands here 
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
    return ADMIN_EACH_HOMEWORK

def admin_confirmation_state(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    confirmation_action = context.user_data['confirmation_action']
    # Delete if confirmed
    if text == CONFIRM_KEYWORD:
        token = context.user_data['token']
        # DELETE HW
        if confirmation_action == 'HW_DELETE':
            id_to_delete = context.user_data['selected_hw_id']
            response,status = delete_with_auth(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=id_to_delete), token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
                return ADMIN_EACH_HOMEWORK
            update.message.reply_text(text='Homework deleted successfully!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
        # DELETE RESOURCE
        elif confirmation_action == 'RES_DELETE':
            id_to_delete = context.user_data['selected_res_id']
            response,status = delete_with_auth(ApiUrls.ADMIN_RESOURCES_WITH_ID.value.format(id=id_to_delete), token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
                return ADMIN_EACH_RESOURCE
            update.message.reply_text(text='Resource deleted successfully!', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY

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
        selected_hw_id = context.user_data['selected_hw_id']
        token = context.user_data['token']
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
    action = context.user_data['action']
    # if the action is 'create' we must get the entered text. if the action is 'update' we must get the entered text unless it is 'skip'.
    if (action == 'update' and text != SKIP_KEYWORD) or (action == 'create'):
        context.user_data['homework_input']['title'] = text

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
        context.user_data['homework_input']['file'] = f'./downloads/{file_name}'
    # If user enters shit
    elif text != SKIP_KEYWORD:
        update.message.reply_text('please send the homework file or skip!', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_FILE

    action = context.user_data['action']
    if action == 'update':
        update.message.reply_text('Now, please set the homework due date or skip to keep the previous deadline.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=SKIP_CANCEL_KEYBOARD)
    elif action == 'create':
        update.message.reply_text('Now, please set the homework due date.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=CANCEL_KEYBOARD)
    return ADMIN_HOMEWORKS_DUE_DATE

def admin_homeworks_due_date(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.user_data['action']
    #if the date time is valid we must convert it to gregorian date time
    if is_valid_date_time(text):
        context.user_data['homework_input']['due_date_time'] = jalali_to_gregorian(text)
    # if user enters shit
    elif action == 'create':
        update.message.reply_text('Please enter a valid date time.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE
    elif action == 'update' and text != SKIP_KEYWORD:
        update.message.reply_text('Now, please set the homework due date or skip to keep the previous deadline.\nformat: yyyy-mm-dd hh:mm:ss', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE

    token = context.user_data['token']
    data = context.user_data['homework_input']
    # Send update request if action is update
    if action == 'update':
        selected_hw_id = context.user_data['selected_hw_id']
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
    categories = context.user_data['categories']
    # Save selected category id in local storage to use it later in requests.
    if text[:-2] in categories.keys():
        context.user_data['selected_cat_id'] = categories[text[:-2]]
        update.message.reply_text(f'What do you want to do with this category?', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_CATEGORIES

def admin_each_category(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.user_data['token']
    # Change status of the category for timeline
    if text == 'Change Status':
        selected_cat_id = context.user_data['selected_cat_id']
        response, status = put_with_auth(ApiUrls.ADMIN_CATEGORY_TOGGLE_STATUS.value.format(id=selected_cat_id), token)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY
        update.message.reply_text(text=f"Category status changed to {'✅' if response['is_taught'] else '❌'}", reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY
    # Manage current resources of the category
    elif text == 'Manage Current Resources':
        selected_cat_id = context.user_data['selected_cat_id']
        response, status = get_with_auth(ApiUrls.ADMIN_CATEGORY_RESOURCES.value.format(id=selected_cat_id), token)
        if status != 200:
            update.message.reply_text(text='Oops! Something went wrong!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        # Creating buttons using retrieved homeworks and store homeworks id in local storage to use later.
        if len(response) == 0:
            update.message.reply_text(text='Timeline not available!', reply_markup=ADMIN_MAIN_KEYBOARD)
            return ADMIN_LOGGED_IN
        
        keyboard_buttons = []
        context.user_data['resources'] = dict()
        for i,res in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {res['title']}")
            context.user_data['resources'][f"{i+1}) {res['title']}"] = res['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Which resource do you want to change??', reply_markup=keyboard)
        return ADMIN_GET_RESOURCES
    # Add a new Resource
    elif text == 'Add a New Resource':
        context.user_data['resource_input'] = dict()
        context.user_data['action'] = 'create'
        update.message.reply_text(text='Please enter the resource title!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_RESOURCE_TITLE

    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_EACH_CATEGORY

def admin_get_resources(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    resources = context.user_data['resources']
    # Save selected resource id in local storage to use it later in requests.
    if text in resources.keys():
        context.user_data['selected_res_id'] = resources[text]
        update.message.reply_text(f'What do you want to do with this resource?', reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
        return ADMIN_EACH_RESOURCE

    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_RESOURCES

def admin_each_resource(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.user_data['token']
    selected_res_id = context.user_data['selected_res_id']
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
        context.user_data['confirmation_action'] = 'RES_DELETE'
        update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
        return ADMIN_CONFIRMATION_STATE
    # Navigate to update section
    elif text == 'Update Resource':
        context.user_data['resource_input'] = dict()
        context.user_data['action'] = 'update'
        update.message.reply_text(text='Please enter the resource title or use skip to keep the previous value.', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_RESOURCE_TITLE
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!')
    return ADMIN_GET_RESOURCES

def admin_resource_title(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.user_data['action']
    # if the action is 'create' we must get the entered text. if the action is 'update' we must get the entered text unless it is 'skip'.
    if (action == 'update' and text != SKIP_KEYWORD) or (action == 'create'):
        context.user_data['resource_input']['title'] = text

    if action == 'update':
        update.message.reply_text('Now, please send the resource link or skip to keep the previous link.', reply_markup=SKIP_CANCEL_KEYBOARD)
    elif action == 'create':
        update.message.reply_text('Now, please send the resource link.', reply_markup=CANCEL_KEYBOARD)
    return ADMIN_RESOURCE_LINK

def admin_resource_link(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    action = context.user_data['action']
    #if the date time is valid we must convert it to gregorian date time
    if re.fullmatch(URL_REGEX, text):
        context.user_data['resource_input']['link'] = text
    # if user enters shit
    elif action == 'create': 
        update.message.reply_text('Please enter a valid URL!', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE
    elif action == 'update' and text != SKIP_KEYWORD:
        update.message.reply_text('Please enter a valid URL or skip to keep the previous link!', reply_markup=SKIP_CANCEL_KEYBOARD)
        return ADMIN_HOMEWORKS_DUE_DATE

    token = context.user_data['token']
    data = context.user_data['resource_input']
    # Send update request if action is update
    if action == 'update':
        patch_data = dict()
        for key,value in data.items():
            if value is not None:
                patch_data[key] = value

        selected_res_id = context.user_data['selected_res_id']
        response, status = patch_with_auth_and_body(ApiUrls.ADMIN_RESOURCES_WITH_ID.value.format(id=selected_res_id), token, patch_data)
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
            return ADMIN_EACH_RESOURCE
        update.message.reply_text(text='Resource updated successfully!', reply_markup=ADMIN_EACH_RESOURCE_KEYBOARD)
        return ADMIN_EACH_RESOURCE
    # Send post request if action is create
    elif action == 'create':
        selected_cat_id = context.user_data['selected_cat_id']
        response, status = post_with_auth(ApiUrls.ADMIN_CATEGORY_RESOURCES.value.format(id=selected_cat_id), token, title=data['title'], link=data['link'])
        if status != 200:
            update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
            return ADMIN_EACH_CATEGORY
        update.message.reply_text(text='Resource created successfully!', reply_markup=ADMIN_EACH_CATEGORY_KEYBOARD)
        return ADMIN_EACH_CATEGORY

def admin_incoming_notifs(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    token = context.user_data['token']
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

            ADMIN_INCOMIG_NOTIFS: [MessageHandler((Filters.text & ~ Filters.command), admin_incoming_notifs)],

            ADMIN_CONFIRMATION_STATE: [MessageHandler((Filters.text & ~ Filters.command), admin_confirmation_state)]
            
        },
        fallbacks=[MessageHandler(Filters.command & Filters.regex('/cancel'), cancel)],
        allow_reentry=False
    )

dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()     