from os import stat

from request_util import ApiUrls,post,get_with_auth

import environ
env = environ.Env()
environ.Env.read_env()

# A decorator to use in functions that user needs to be authorized before
def is_authorized(func):

    def wrapper_func(update, context, **kwargs):
        if 'token' in context.chat_data.keys():
            token = context.chat_data['token']
            return func(update, context, token=token, **kwargs)
        else:
            update.message.reply_text('You are not logged in yet! Use /login command!')

    return wrapper_func

# A decorator to use in functions that user needs to log out before
def not_authorized(func):
    
    def wrapper_func(update, context, **kwargs):
        if 'token' not in context.chat_data.keys():
            return func(update,context,**kwargs)
        else:
            update.message.reply_text('You must /logout before this operation')

    return wrapper_func

# A decorator to get user last login if needed
def get_last_login(func):

    def wrapper_func(update, context, **kwargs):
        token = context.bot_data.get('token', None)
        if token is None:
            email = env('BOT_API_EMAIL')
            password = env('BOT_API_PASSWORD')
            response,status = post(ApiUrls.LOGIN.value, username=email, password=password, chat_id=0)
            if status != 200:
                update.message.reply_text(text='Oops sth went wrong!')
                return 
            token = response['token']
            context.bot_data['token'] = token

        if 'token' not in context.chat_data.keys():
            response, status = get_with_auth(ApiUrls.LAST_LOGIN.value, token, chat_id=update.effective_chat.id)
            if status != 200:
                update.message.reply_text(text='Oops sth went wrong!')
                return 

            if response['token'] is not None:
                context.chat_data['token'] = response['token']
                context.chat_data['is_admin'] = response['is_admin']

                # Get question data if is admin
                if response['is_admin']:
                    response, status = get_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_GET_DATA.value, response['token'], chat_id=update.effective_chat.id)
                    if status != 200:
                        update.message.reply_text(text='Oops sth went wrong!')
                        return 

                    if context.bot_data.get('questions_data', None) is None: 
                        context.bot_data['questions_data'] = dict()
                    chat_id = update.effective_chat.id
                    context.bot_data['questions_data'][chat_id] = dict()
                    for key,value in response.items():
                        context.bot_data['questions_data'][chat_id][key] = value

        return func(update,context,**kwargs)
    
    return wrapper_func