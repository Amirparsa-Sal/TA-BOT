import telegram
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import environ
import re

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
REGISTER_ENTER_EMAIL, REGISTER_ENTER_OTP, LOGIN_ENTER_EMAIL, LOGIN_ENTER_PASSWORD = range(4)

# REGEX
SIMPLE_EMAIL_REGEX = '^[^@\s]+@[^@\s]+\.[^@\s]+$'
AUT_EMAIL_REGEX = '^[A-Za-z0-9._%+-]+@aut\.ac\.ir'
OTP_REGEX = '^[0-9]{5}'

def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='Hi! Use /Register or /Login to start using the bot.')
    return ConversationHandler.END

def register(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='We are in register section. You can use /cancel to cancel the operation in each section.\n Now, Please enter your AUT email!')
    return REGISTER_ENTER_EMAIL

def login(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='We are in login section. You can use /cancel to cancel the operation in each section.\n Now, Please enter your email!')
    return LOGIN_ENTER_EMAIL

def register_enter_email(update: telegram.Update, context: telegram.ext.CallbackContext):
    if re.fullmatch(AUT_EMAIL_REGEX, update.message.text):
        context.user_data['email'] = update.message.txt #Saving the email to use it in next request
        #TODO: Sent the otp
        update.message.reply_text(text=f'Otp sent to {update.message.text}. Please enter the otp:')
        return REGISTER_ENTER_OTP
    update.message.reply_text(text='This is not an AUT email dude! Please re enter your email!')
    return REGISTER_ENTER_EMAIL

def register_enter_otp(update: telegram.Update, context: telegram.ext.CallbackContext):
    if re.fullmatch(OTP_REGEX, update.message.text):
        email = context.user_data['email']
        #TODO: Check the otp correctness given the email and otp
        update.message.reply_text(text='Register completed!')
        return ConversationHandler.END
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
    #TODO: Send the login request with given password and email and check if the status code is ok
    update.message.reply_text(text='Logged in successfully!')
    return ConversationHandler.END

def cancel(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text(text='Operation Canceled!')
    return ConversationHandler.END

conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('register', register), CommandHandler('login', login)],
        states={
            # REGISTER STATES
            REGISTER_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), register_enter_email)],
            REGISTER_ENTER_OTP: [MessageHandler((Filters.text & ~ Filters.command), register_enter_otp)],
            
            # LOGIN STATES
            LOGIN_ENTER_EMAIL: [MessageHandler((Filters.text & ~ Filters.command), login_enter_email)],
            LOGIN_ENTER_PASSWORD: [MessageHandler((Filters.text & ~ Filters.command), login_enter_password)],
            
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
updater.start_polling()