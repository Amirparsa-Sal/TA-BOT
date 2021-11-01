from typing import Iterable
from telegram import ReplyKeyboardMarkup,KeyboardButton

def create_vertical_keyboard(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

CANCEL_COMMAND = '/cancel'
def create_vertical_keyboard_with_cancel_button(buttons: Iterable):
    keyboard = [[KeyboardButton(button)] for button in buttons]
    keyboard.append([KeyboardButton(CANCEL_COMMAND)])
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
CANCEL_KEYBOARD = create_vertical_keyboard_with_cancel_button([])

### MAIN KEYBOARDS 
REGISTER_KEYWORD = 'ثبت نام'
LOGIN_KEYWORD = 'ورود'
NOT_LOGGED_IN_KEYBOARD = create_vertical_keyboard([REGISTER_KEYWORD, LOGIN_KEYWORD])

HOMEWORKS_KEYWORD = 'تمارین'
TIMELINE_RESOURCES_KEYWORD = 'مباحث درس و منابع'
QUESTIONS_KEYWORD = 'سوالات'
SEND_NOTIF_KEYWORD = 'ارسال نوتیفیکیشن'
INCOMING_NOTIF_KEYWORD = 'نوتیفیکیشن های دریافتی'
LOGOUT_KEYWORD = 'خروج از حساب'
ADMIN_MAIN_KEYBOARD = create_vertical_keyboard([HOMEWORKS_KEYWORD, TIMELINE_RESOURCES_KEYWORD, QUESTIONS_KEYWORD, SEND_NOTIF_KEYWORD, \
                                                INCOMING_NOTIF_KEYWORD, LOGOUT_KEYWORD])

GRADES_KEYWORD = 'نمرات'
RESOURCES_KEYWORD = 'منابع'
TIMELINE_KEYWORD = 'مباحث درس'
MEMBER_MAIN_KEYBOARD = create_vertical_keyboard([QUESTIONS_KEYWORD, HOMEWORKS_KEYWORD, GRADES_KEYWORD, RESOURCES_KEYWORD, \
                                                 TIMELINE_KEYWORD, LOGOUT_KEYWORD])

### CONFIRMATION KEYBOARD
CONFIRM_KEYWORD = 'آره'
DECLINE_KEYWORD = 'نه'
CONFIRMATION_KEYBOARD = ReplyKeyboardMarkup(
    [
    [CONFIRM_KEYWORD,DECLINE_KEYWORD]
    ],
    one_time_keyboard=True
)

### SKIP CANCEL KEYBOARD
SKIP_KEYWORD = '/skip'
SKIP_CANCEL_KEYBOARD = create_vertical_keyboard_with_cancel_button([SKIP_KEYWORD])

### ADMIN HOMEWORK KEYBOARDS
MANAGE_HOMEWORKS_KEYWORD = 'مدیریت تمارین'
CREATE_HOMEWORK_KEYWORD = 'ایجاد تمرین جدید'
ADMIN_HOMEWORKS_MAIN_KEYBOARD = create_vertical_keyboard_with_cancel_button([MANAGE_HOMEWORKS_KEYWORD, CREATE_HOMEWORK_KEYWORD])

HOMEWORK_DETAILS_KEYWORD = 'مشاهده ی اطلاعات تمرین'
HOMEWORK_DELETE_KEYWORD = 'حذف تمرین'
HOMEWORK_UPDATE_KEYWORD = 'آپدیت تمرین'
HOMEWORK_UPDATE_GRADES_KEYWORD = 'آپدیت نمرات تمرین'
HOMEWORK_PUBLISH_KEYWORD = 'منتشر کردن تمرین'
HOMEWORK_UNPUBLISH_KEYWORD = 'مخفی کردن تمرین'
HOMEWORK_PUBLISH_GRADES_KEYWORD = 'منتشر کردن نمرات تمرین'
HOMEWORK_UNPUBLISH_GRADES_KEYWORD = 'مخفی کردن نمرات تمرین'
ADMIN_EACH_HW_KEYBOARD = ReplyKeyboardMarkup(
    [
    [HOMEWORK_DETAILS_KEYWORD],
    [HOMEWORK_DELETE_KEYWORD, HOMEWORK_UPDATE_KEYWORD, HOMEWORK_UPDATE_GRADES_KEYWORD], 
    [HOMEWORK_PUBLISH_KEYWORD, HOMEWORK_UNPUBLISH_KEYWORD],
    [HOMEWORK_PUBLISH_GRADES_KEYWORD, HOMEWORK_UNPUBLISH_GRADES_KEYWORD],
    [CANCEL_COMMAND]   
    ]
)

### ADMIN TIMELINE & RESOURCES KEYBOARDS
CATEGORY_CHANGE_STATUS_KEYWORD = 'تغییر وضعیت'
CATEGORY_MANAGE_RESOURCES_KEYWORD = 'مدیریت منابع'
CATEGORY_ADD_RESOURCE_KEYWORD = 'اضافه کردن منبع'
ADMIN_EACH_CATEGORY_KEYBOARD = create_vertical_keyboard_with_cancel_button([CATEGORY_CHANGE_STATUS_KEYWORD, CATEGORY_MANAGE_RESOURCES_KEYWORD, \
                                                                            CATEGORY_ADD_RESOURCE_KEYWORD])

RESOURCE_DETAILS_KEYWORD = 'مشاهده ی اطلاعات منبع'
RESOURCE_UPDATE_KEYWORD = 'آپدیت منبع'
RESOURCE_DELETE_KEYWORD = 'حذف منبع'
ADMIN_EACH_RESOURCE_KEYBOARD = create_vertical_keyboard_with_cancel_button([RESOURCE_DETAILS_KEYWORD, RESOURCE_UPDATE_KEYWORD, \
                                                                            RESOURCE_DELETE_KEYWORD])


### ADMIN INCOMING NOTIFS KEYBOARD
ENABLE_KEYWORD = 'فعالش کن'
DISABLE_KEYWORD = 'غیر فعالش کن'
ADMIN_INCOMING_NOTIFS_KEYBOARD = ReplyKeyboardMarkup(
    [
        [ENABLE_KEYWORD, DISABLE_KEYWORD]
    ],
    one_time_keyboard=True
)

### ADMIN QUESTIONS
ALL_UNANSWERED_QUESTIONS_KEYWORD = 'سوالات بدون پاسخ'
ALL_ANSWERED_QUESTIONS_KEYWORD = 'سوالات پاسخ داده شده'
ADMIN_QUESTIONS_KEYBOARD = create_vertical_keyboard_with_cancel_button([ALL_UNANSWERED_QUESTIONS_KEYWORD, ALL_ANSWERED_QUESTIONS_KEYWORD])

### MEMBER QUESTIONS
ASK_QUESTION_KEYWORD = 'پرسیدن سوال جدید'
MY_QUESTIONS_KEYWORD = 'سوالات من'
MEMBER_QUESTIONS_KEYBOARD = create_vertical_keyboard_with_cancel_button([ASK_QUESTION_KEYWORD, MY_QUESTIONS_KEYWORD])

############ MESSAGES #############

### GENERAL
HI_MESSAGE = 'سلام. به ربات تدریسیاری درس مبانی برنامه نویسی خوش اومدی! برای شروع به کار یکی از گزینه های زیر رو انتخاب کن.'
OPERATION_CANCELED_MESSAGE = 'عملیات لغو شد!'
CHOOSE_FROM_KEYBOARD_MESSAGE = 'لطفا یکی از گزینه های زیر رو انتخاب کن!'
STH_WENT_WRONG_MESSAGE = 'ای بابا! یه مشکلی پیش اومد. نتونستم انجامش بدم.'
NO_DATA_MESSAGE = 'در حال حاضر اطلاعاتی تو این بخش وجود نداره!'
LOGOUT_MESSAGE = 'شما با موفقیت از حساب خارج شدین.'
WAIT_MESSAGE = 'اندکی صبر...'
ARE_YOU_SURE_MESSAGE = 'مطمئنی؟'

### VALIDATION
NOT_AN_AUT_EMAIL_MESSAGE = 'این ایمیل مال aut نیست عزیز! لطفا ایمیل دانشگاهیت رو بفرست!'
NOT_AN_EMAIL_MESSAGE = 'این چیزی که وارد کردی اصن ایمیل نیست! لطفا یه ایمیل معتبر وارد کن.'
NOT_CORRECT_OTP_FORMAT_MESSAGE = 'رمز یک بار مصرف یه عدد ۵ رقمیه! یه دور دیگه واردش کن.'
NOT_AN_URL_MESSAGE = 'چیزی که وارد کردی لینک نیست! لطفا یه لینک معتبر بفرست.'
DIDNT_UNDERSTAND_MESSAGE = 'ببخشید؟ متوجه نشدم!'

### AUTH
REGISTER_COMPLETED_MESSAGE = 'ثبت نام با موفقیت انجام شد!'
SEND_EMAIL_MESSAGE = 'لطفا ایمیلت رو برام بفرست!'
SEND_PASSWORD_MESSAGE = 'حالا لطفا رمزت رو برام بفرست. این رمز به صورت پیش فرض برابر با شماره دانشجویی شماست.'
ENTER_SECRET_MESSAGE = 'واسه اینکه خودتو ثابت کنی بگو ببینم رمز مخفی بین ادمینا چیه؟'
LOGIN_AS_ADMIN_MESSAGE = 'شما به عنوان ادمین وارد شدید!'
LOGIN_AS_STUDENT_MESSAGE = 'با موفقیت وارد شدی :)'
WRONG_CREDENTIALS_MESSAGE = 'ایمیل یا رمز عبور رو اشتباه وارد کردی! حالا دوباره از اول ایمیل رو برام بفرست.'
WRONG_SECRET = 'رمز مخفی رو اشتباه وارد کردی! دوباره بفرستش اگه راست میگی!'
ADMIN_ACCESS_ACTIVATED_MESSAGE = 'دسترسی ادمین برای این ایمیل فعال شد!'
OTP_SENT_MESSAGE = 'رمز یک بار مصرف به ایمیل ارسال شد. لطفا اونو برام بفرست!'

#### ADMIN HOMEWORKS
ADMIN_HOMEWORKS_MAIN_MESSAGE = 'شما در بخش تمارین هستید!'
ADMIN_HOMEWORK_ENTER_TITLE_MESSAGE = 'لطفا عنوان تمرین رو وارد کن.'
ADMIN_HOMEWORK_ENTER_TITLE_OR_SKIP_MESSAGE = 'لطفا عنوان تمرین رو برام بفرست یا از /skip استفاده کن تا عنوانش همون عنوان قبلی باشه.'
ADMIN_HOMEWORK_SEND_FILE_MESSAGE = 'حالا برام فایل تمرین رو بفرست یا از /skip استفاده کن و بعدا آپلودش کن.'
ADMIN_HOMEWORK_SEND_FILE_OR_SKIP_MESSAGE = 'حالا برام فایل تمرین رو بفرست یا از /skip استفاده کن که همون فایل قبلی سر جاش بمونه.'
ADMIN_HOMEWORK_ENTER_DUE_DATE_MESSAGE = 'حالا برام تاریخ ددلاین تمرین رو با یه تاریخ شمسی به شکل yyyy-mm-dd hh:mm:ss بفرست.'
ADMIN_HOMEWORK_ENTER_DUE_DATE_OR_SKIP_MESSAGE = 'حالا برام تاریخ ددلاین رو با یه تاریخ شمسی به شکل yyyy-mm-dd hh:mm:ss بفرست یا از /skip استفاده کن تا همون تاریخ قبلی باقی بمونه.'

ADMIN_EACH_HOMEWORK_MESSAGE = 'میخوای با این تمرین چیکار کنی؟'
UPLOADING_MESSAGE = 'در حال آپلود فایل...'
HOMEWORK_IS_PUBLISHED_MESSAGE = 'تمرین با موفقیت منتشر شد.'
HOMEWORK_IS_UNPUBLISHED_MESSAGE = 'تمرین مخفی شد.'
HOMEWORK_GRADES_ARE_PUBLISHED_MESSAGE = 'نمرات تمرین با موفقیت منتشر شد.'
HOMEWORK_GRADES_ARE_UNPUBLISHED_MESSAGE = 'نمرات تمرین مخفی شد.'
HOMEWORK_DELETED_MESSAGE = 'تمرین با موفقیت حذف شد.'
HOMEWORK_UPDATED_MESSAGE = 'تمرین با موفقیت آپدیت شد.'
HOMEWORK_CREATED_MESSAGE = 'تمرین با موفقیت ایجاد شد.'
GRADES_UPDATED_MESSAGE = 'نمرات با موفقیت آپدیت شدن.'
ENTER_GRADES_LINK_MESSAGE = 'لطفا لینک نمرات تمرین رو برام بفرست.'

#### ADMIN QUESTIONS
ADMIN_QUESTIONS_MAIN_MESSAGE = 'شما در بخش سوالات هستید!'
NEW_QUESTION_MESSAGE = 'سوال از طرف {user}:\n\n{text}'
QUESTIONS_ARE_SENT_MESSAGE = 'همه ی سوالا ارسال شدن!'
CHOOSE_QUESTION_AND_REPLY_MESSAGE = 'می تونی با ریپلای کردن هر سوال و نوشتن جوابش بعد از دستور /answer به سوالات جواب بدی!'
FAILED_TO_FORWARD_ANSWER_MESSAGE = 'نتونستم جواب رو ارسال کنم :('
FAILED_TO_FORWARD_ANSWER_TO_MESSAGE = 'نتونستم جواب رو به {user}براش ارسال کنم :('
ANSWER_WERE_SENT_MESSAGE = 'پاسخ با موفقیت به اکانت های زیر ارسال شد:\n\n'

### MEMBER QUESTIONS
SEND_YOUR_QUESTION_MESSAGE = 'لطفا سوالت رو برام بفرست!'
HAVE_NOT_ASKED_QUESTIONS_MESSAGE = 'تا حالا هیچ سوالی نپرسیدی!'
CHOOSE_QUESTION_MESSAGE = 'لطفا یه سوال رو انتخاب کن. اونایی که جلوشون تیک خورده پاسخ داده شدن.'
QUESTION_DETAILS_MESSAGE = 'سوال:\n{question}\n\nپاسخ:\n{answer}'
QUESTION_SENT_MESSAGE = 'سوالت رو برای تدریسیار ها ارسال کردم. هر وقت جوابت رو دادن برات فورواردش می کنم.'
NEW_ANSWER_MESSAGE = 'یه جواب جدید برای سوالت اومده!\n\nسوال:\n{question}\n\nپاسخ:\n{answer}'

#### ADMIN NOTIF
ADMIN_SEND_NOTIF_MESSAGE = 'لطفا متن نوتیفیکیشن رو برام بفرست!'
ADMIN_INCOMING_NOTIF_MAIN_MESSAGE = 'نوتیفیکیش های دریافتی در حال حاضر {status} هستن! می خوای چیکارشون کنی؟'
NOTIF_SENT_MESSAGE = 'نوتیفیکیشن برای همه ارسال شد!'
NOTIF_FAILED_MESSAGE = 'نوتیفیکیشن برای {success} نفر از {total} دانشجو ارسال شد.\nاکانت هایی که براشون ارسال نشد:\n\n'
NOTIF_ACTIVATED_MESSAGE = 'دریافت نوتیفیکیشن برای سوالات فعال شد!'
NOTIF_DISABLED_MESSAGE = 'دریافت نوتیفیکیشن برای سوالات غیرفعال شد!'

#### ADMIN CATEGORIES
ADMIN_EACH_CATEGORY_MESSAGE = 'میخوای با این مبحث چیکار کنی؟'

### MEMBER NOTIF
NEW_NOTIF_MESSAGE = 'یه نوتیفیکیشن جدید اومده:\n\n{text}'

### CATEGORIES
CHOOSE_CATEGORY_MESSAGE = 'لطفا یکی از مباحث زیر رو انتخاب کن!'
CATEGORY_CHANGE_STATUS_MESSAGE = 'وضعیت این مبحث به {status} تغییر کرد.'

### RESOURCES
CHOOSE_RESOURCE_MESSAGE = 'لطفا یکی از منابع زیر رو انتخاب کن.'
ADMIN_RESOURCE_ENTER_TITLE_MESSAGE = 'یه عنوان برای منبع بفرست برام!'
ADMIN_RESOURCE_ENTER_TITLE_OR_SKIP_MESSAGE = 'یه عنوان برای منبع بفرست برام یا از /skip استفاده کن تا عنوان قبلی حفظ بشه.'
ADMIN_RESOURCE_ENTER_LINK_MESSAGE = 'حالا یه لینک برای منبع بفرست برام!'
ADMIN_RESOURCE_ENTER_LINK_OR_SKIP_MESSAGE = 'حالا یه لینک برای منبع بفرست برام یا از /skip استفاده کن تا عنوان قبلی حفظ بشه.'
ADMIN_EACH_RESOURCE_MESSAGE = 'میخوای با این منبع چیکار کنی؟'
LIST_OF_RESOURCES_MESSAGE = 'لیست منابع:\n\n'

RESOURCE_DETAILS_MESSAGE = 'عنوان:\n{title}\n\nلینک:\n{link}'
RESOURCE_UPDATED_MESSAGE = 'منبع با موفقیت آپدیت شد'
RESOURCE_CREATED_MESSAGE = 'منبع با موفقیت ایجاد شد.'
RESOURCE_DELETED_MESSAGE = 'منبع با موفقیت حذف شد.'

### HOMEWORK
CHOOSE_HOMEWORK_MESSAGE = 'لطفا یکی از تمارین زیر رو انتخاب کن!'
