from typing import Iterable
from telegram import ReplyKeyboardMarkup,KeyboardButton

CANCEL_COMMAND = '/cancel'
CONFIRM_KEYWORD = 'Yes'
DECLINE_KEYWORD = 'No'

def create_vertical_keyboard(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

def create_vertical_keyboard_with_cancel_button(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    keyboard.append([KeyboardButton(CANCEL_COMMAND)])
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

# MAIN KEYBOARDS 

NOT_LOGGED_IN_KEYBOARD = create_vertical_keyboard(['Register', 'Login'])

ADMIN_MAIN_KEYBOARD = create_vertical_keyboard(['Homeworks', 'Resources', 'Timeline', 'Send Notifications', \
                                                'Incoming Notifications', 'Logout'])

MEMBER_MAIN_KEYBOARD = create_vertical_keyboard(['Ask Question', 'Homeworks', 'Resources', 'Timeline', 'Logout'])

CANCEL_KEYBOARD = create_vertical_keyboard_with_cancel_button([])

CONFIRMATION_KEYBOARD = ReplyKeyboardMarkup(
    [
    [CONFIRM_KEYWORD,DECLINE_KEYWORD]
    ],
    one_time_keyboard=True
)
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