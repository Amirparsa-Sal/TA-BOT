from os import stat_result
from django.http import response
import telegram
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import environ
import re
from request_util import *
from json import loads
from decorators import not_authorized,is_authorized,get_last_login
from keyboards import *
from date_utils import *

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
ADMIN_HOMEWORKS_MAIN, ADMIN_MANAGE_HOMEWORKS, ADMIN_EACH_HOMEWORK, ADMIN_CREATE_HOMEWORKS_TITLE, ADMIN_CREATE_HOMEWORKS_FILE, \
ADMIN_CREATE_HOMEWORKS_DUE_DATE,\
ADMIN_UPDATE_GRADE_ENTER_LINK, \
ADMIN_CONFIRMATION_STATE, \
MEMBER_TIMELINE = range(18)

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
        keyboard_buttons = []
        context.user_data['homeworks'] = dict()
        for i,hw in enumerate(response):
            keyboard_buttons.append(f"{i+1}) {hw['title']}")
            context.user_data['homeworks'][f"{i+1}) {hw['title']}"] = hw['id']

        keyboard = create_vertical_keyboard_with_cancel_button(keyboard_buttons)
        update.message.reply_text(text='Please choose the homework you want.', reply_markup=keyboard)
        return ADMIN_MANAGE_HOMEWORKS
        
    # TODO: Navigate to create homework section
    elif text == 'Create a New Homework':
        pass
    
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
        context.user_data['object_to_delete'] = 'HW'
        update.message.reply_text(text='Are you sure?', reply_markup=CONFIRMATION_KEYBOARD)
        return ADMIN_CONFIRMATION_STATE
    # Navigate to update Grade
    elif text == 'Update HW Grades':
        update.message.reply_text(text='Please enter the link of the grades.', reply_markup=CANCEL_KEYBOARD)
        return ADMIN_UPDATE_GRADE_ENTER_LINK

    #TODO: add other commands here 
    # Stay at this state if the user enters shit
    update.message.reply_text(text='Sorry I didnt understand!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
    return ADMIN_EACH_HOMEWORK

def admin_confirmation_state(update: telegram.Update, context: telegram.ext.CallbackContext):
    text = update.message.text
    # Delete if confirmed
    if text == CONFIRM_KEYWORD:
        token = context.user_data['token']
        object_to_delete = context.user_data['object_to_delete']
        if object_to_delete == 'HW':
            id_to_delete = context.user_data['selected_hw_id']
            response,status = delete_with_auth(ApiUrls.ADMIN_HOMEWORK_WITH_ID.value.format(id=id_to_delete), token)
            if status != 200:
                update.message.reply_text(text=response['detail'], reply_markup=ADMIN_EACH_HW_KEYBOARD)
                return ADMIN_EACH_HOMEWORK
            update.message.reply_text(text='Homework deleted successfully!', reply_markup=ADMIN_HOMEWORKS_MAIN_KEYBOARD)
            return ADMIN_HOMEWORKS_MAIN
    elif text == DECLINE_KEYWORD:
        update.message.reply_text(text='Operation canceled!', reply_markup=ADMIN_EACH_HW_KEYBOARD)
        return ADMIN_EACH_HOMEWORK

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

conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler((Filters.text & ~ Filters.command), entry_message_handler)],
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
            # ADMIN_CREATE_HOMEWORKS_TITLE: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_email)],
            # ADMIN_CREATE_HOMEWORKS_FILE: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_email)],
            # ADMIN_CREATE_HOMEWORKS_DUE_DATE: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_email)],
            ADMIN_UPDATE_GRADE_ENTER_LINK: [MessageHandler((Filters.text & ~ Filters.command), admin_update_grade_enter_link)],

            ADMIN_CONFIRMATION_STATE: [MessageHandler((Filters.text & ~ Filters.command), admin_confirmation_state)]
            
        },
        fallbacks=[MessageHandler(Filters.command & Filters.regex('/cancel'), cancel)],
        allow_reentry=False
    )

dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()     