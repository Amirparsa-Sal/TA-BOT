from typing import Iterable
from telegram import ReplyKeyboardMarkup,KeyboardButton

CANCEL_COMMAND = '/cancel'
CONFIRM_KEYWORD = 'Yes'
DECLINE_KEYWORD = 'No'
SKIP_KEYWORD = 'Skip'
ENABLE_KEYWORD = 'Enable'
DISABLE_KEYWORD = 'Disable'

def create_vertical_keyboard(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

def create_vertical_keyboard_with_cancel_button(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    keyboard.append([KeyboardButton(CANCEL_COMMAND)])
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

# MAIN KEYBOARDS 

NOT_LOGGED_IN_KEYBOARD = create_vertical_keyboard(['Register', 'Login'])

ADMIN_MAIN_KEYBOARD = create_vertical_keyboard(['Homeworks', 'Timeline & Resources', 'Questions', 'Send Notifications', \
                                                'Incoming Notifications', 'Logout'])

MEMBER_MAIN_KEYBOARD = create_vertical_keyboard(['Questions', 'Homeworks', 'Grades', 'Resources', 'Timeline', 'Logout'])

CANCEL_KEYBOARD = create_vertical_keyboard_with_cancel_button([])

CONFIRMATION_KEYBOARD = ReplyKeyboardMarkup(
    [
    [CONFIRM_KEYWORD,DECLINE_KEYWORD]
    ],
    one_time_keyboard=True
)

SKIP_CANCEL_KEYBOARD = create_vertical_keyboard_with_cancel_button([SKIP_KEYWORD])

# ADMIN HOMEWORK KEYBOARDS

ADMIN_HOMEWORKS_MAIN_KEYBOARD = create_vertical_keyboard_with_cancel_button(['Manage Current Homeworks', 'Create a New Homework'])

ADMIN_EACH_HW_KEYBOARD = ReplyKeyboardMarkup(
    [
    ['Homework Details'],
    ['Delete HW', 'Update HW', 'Update HW Grades'], 
    ['Publish HW', 'Unpublish HW'],
    ['Publish Grades', 'Unpublish Grades'],
    ['/cancel']   
    ]
)

# ADMIN TIMELINE & RESOURCES KEYBOARDS
ADMIN_EACH_CATEGORY_KEYBOARD = create_vertical_keyboard_with_cancel_button(['Change Status', 'Manage Current Resources', 'Add a New Resource'])
ADMIN_EACH_RESOURCE_KEYBOARD = create_vertical_keyboard_with_cancel_button(['Get Resource Details', 'Update Resource', 'Delete Resource'])

# ADMIN INCOMING NOTIFS KEYBOARD
ADMIN_INCOMING_NOTIFS_KEYBOARD = ReplyKeyboardMarkup(
    [
        [ENABLE_KEYWORD, DISABLE_KEYWORD]
    ],
    one_time_keyboard=True
)

# ADMIN QUESTIONS
ADMIN_QUESTIONS_KEYBOARD = create_vertical_keyboard_with_cancel_button(['Get All Unanswered Questions', 'Get All Answered Questions'])

# MEMBER QUESTIONS
MEMBER_QUESTIONS_KEYBOARD = create_vertical_keyboard_with_cancel_button(['Ask a Question', 'My Questions'])