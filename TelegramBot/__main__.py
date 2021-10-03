import telegram
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import environ
import re
from request_util import ApiUrls, post, post_with_auth, get_with_auth, get
from json import loads

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
REGISTER_ENTER_EMAIL, REGISTER_ENTER_OTP, LOGIN_ENTER_EMAIL, LOGIN_ENTER_PASSWORD, \
REGISTER_ADMIN_ENTER_EMAIL, REGISTER_ADMIN_ENTER_SECRET = range(6)

# REGEX
SIMPLE_EMAIL_REGEX = '^[^@\s]+@[^@\s]+\.[^@\s]+$'
AUT_EMAIL_REGEX = '^[A-Za-z0-9._%+-]+@aut\.ac\.ir'
OTP_REGEX = '^[0-9]{5}'

# A decorator to use in functions that user needs to be authorized before
def is_authorized(func):

    def wrapper_func(update, context, **kwargs):
        if 'token' in context.user_data.keys():
            token = context.user_data['token']
            return func(update, context, token=token, **kwargs)
        else:
            update.message.reply_text('You are not logged in yet! Use /login command!')

    return wrapper_func

# A decorator to use in functions that user needs to log out before
def not_authorized(func):
    
    def wrapper_func(update, context, **kwargs):
        if 'token' not in context.user_data.keys():
            return func(update,context,**kwargs)
        else:
            update.message.reply_text('You must /logout before this operation')

    return wrapper_func

# A decorator to get user last login if needed
def get_last_login(func):

    def wrapper_func(update, context, **kwargs):
        if 'token' not in context.user_data.keys():
            response, status = get(ApiUrls.LAST_LOGIN.value, chat_id=update.effective_chat.id)
            if response['token'] is not None:
                context.user_data['token'] = response['token']
        return func(update,context,**kwargs)
    
    return wrapper_func

def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='Hi! Use /Register or /Login to start using the bot.')
    return ConversationHandler.END

def register(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='We are in register section. You can use /cancel to cancel the operation in each section.\n Now, Please enter your AUT email!')
    return REGISTER_ENTER_EMAIL

@not_authorized
def login(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='We are in login section. You can use /cancel to cancel the operation in each section.\n Now, Please enter your email!')
    return LOGIN_ENTER_EMAIL

def register_admin(update: telegram.Update, context: telegram.ext.CallbackContext):
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
            update.message.reply_text(text=f'Otp sent to {update.message.text}. Please enter the otp:')
            return REGISTER_ENTER_OTP
        update.message.reply_text(text=response['detail'])
        return REGISTER_ENTER_EMAIL
    update.message.reply_text(text='This is not an AUT email dude! Please re enter your email!')
    return REGISTER_ENTER_EMAIL

def register_enter_otp(update: telegram.Update, context: telegram.ext.CallbackContext):
    # Check if the otp is valid
    if re.fullmatch(OTP_REGEX, update.message.text):
        email = context.user_data['email']
        #Check the otp correctness given the email and otp
        response, status = post(ApiUrls.ACTIVATE_ACCOUNT.value, email=email, otp=update.message.text)
        if status == 200:
            update.message.reply_text(text='Register completed!')
            return ConversationHandler.END
        update.message.reply_text(text=response['detail'])
        return REGISTER_ENTER_OTP
    update.message.reply_text(text='The OTP format is not correct. it must be a 5 digit number.')
    return REGISTER_ENTER_OTP

def login_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    if re.fullmatch(SIMPLE_EMAIL_REGEX, update.message.text):
        context.user_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter your student id.')
        return LOGIN_ENTER_PASSWORD
    update.message.reply_text(text='This is not an email dude! Please re enter your email!')
    return LOGIN_ENTER_EMAIL

def login_enter_password(update: telegram.Update, context: telegram.ext.CallbackContext):
    email = context.user_data['email']
    response, status = post(ApiUrls.LOGIN.value, username=email, password=update.message.text, chat_id=update.effective_chat.id)
    if status == 200:
        update.message.reply_text(text='Logged in successfully!')
        context.user_data['token'] = response['token']
        return ConversationHandler.END
    update.message.reply_text(text='email or password is not correct. Please enter your email again!')
    return LOGIN_ENTER_EMAIL
        
def register_admin_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    if re.fullmatch(SIMPLE_EMAIL_REGEX, update.message.text):
        context.user_data['email'] = update.message.text #Saving the email to use it in next request
        update.message.reply_text(text='Now, Please enter the secret :)')
        return REGISTER_ADMIN_ENTER_SECRET
    update.message.reply_text(text='This is not an email dude! Please re enter your email!')
    return REGISTER_ADMIN_ENTER_EMAIL

def register_admin_enter_secret(update: telegram.Update, context: telegram.ext.CallbackContext):
    email = context.user_data['email']
    response, status = post(ApiUrls.REGISTER_ADMIN.value, email=email, secret=update.message.text)
    if status == 200:
        update.message.reply_text(text='Admin access activated!')    
        return ConversationHandler.END
    update.message.reply_text(text='The secret is not correct. Please enter the secret again!')
    return REGISTER_ADMIN_ENTER_SECRET

@get_last_login
@is_authorized
def get_timeline(update: telegram.Update, context: telegram.ext.CallbackContext, token=None):
    response, status = get_with_auth(ApiUrls.MEMBER_GET_CATEGORIES.value, token)
    
    # Create message
    message = 'List of all course sections:\n\n'
    for i, category in enumerate(response):
        message += f"{i+1}) {category['title']} -> {'taught' if category['is_taught'] else 'not taught'}\n\n"
    
    update.message.reply_text(text=message)
        

def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='Operation Canceled!')
    return ConversationHandler.END

@is_authorized
def logout(update: telegram.Update, context: telegram.ext.CallbackContext, token=None):
    chat_id = update.effective_chat.id
    response,status = post_with_auth(ApiUrls.LOGOUT.value, token, chat_id=chat_id)
    if status != 200:
        update.message.reply_text(text='Oops! Something went wrong!')
    else:
        del context.user_data['token']
        update.message.reply_text(text='You logged out successfully!')

conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('register', register), CommandHandler('login', login), \
                      CommandHandler('register_admin', register_admin), CommandHandler('timeline', get_timeline)],
        states={
            # REGISTER STATES
            REGISTER_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), register_enter_email)],
            REGISTER_ENTER_OTP: [MessageHandler((Filters.text & ~ Filters.command), register_enter_otp)],
            
            # LOGIN STATES
            LOGIN_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), login_enter_email)],
            LOGIN_ENTER_PASSWORD: [MessageHandler((Filters.text & ~ Filters.command), login_enter_password)],

            # REGISTER_ADMIN STATES
            REGISTER_ADMIN_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_email)],
            REGISTER_ADMIN_ENTER_SECRET: [MessageHandler((Filters.text & ~ Filters.command), register_admin_enter_secret)],
            
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

logout_handler = CommandHandler('logout', logout)

dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(logout_handler)
updater.start_polling()