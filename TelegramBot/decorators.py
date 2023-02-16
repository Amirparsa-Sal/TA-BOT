from os import stat

from request_util import ApiUrls,post,get_with_auth

import environ
env = environ.Env()
environ.Env.read_env()

def get_last_login(func):
    '''A decorator to get user last login if needed'''
    def wrapper_func(update, context, **kwargs):
        token = context.bot_data.get('token', None)
        # if bot token is empty login with bot as superuser
        if token is None:
            # getting email and password
            email = env('BOT_API_EMAIL')
            password = env('BOT_API_PASSWORD')
            # logging in
            response,status = post(ApiUrls.LOGIN.value, username=email, password=password, chat_id=0)
            # if login is not successful rasie error
            if status != 200:
                update.message.reply_text(text='Oops sth went wrong!')
                return 
            # set the bot token
            token = response['token']
            context.bot_data['token'] = token

        # if bot is restarted and the tokens are deleted, check if the user hass logged in before
        if 'token' not in context.chat_data.keys():
            # get the last login of the user
            response, status = get_with_auth(ApiUrls.LAST_LOGIN.value, token, chat_id=update.effective_chat.id)
            # if the request is not successful, raise error
            if status != 200:
                update.message.reply_text(text='Oops sth went wrong!')
                return 
            # if user has logged in before, set the token and role
            if response['token'] is not None:
                context.chat_data['token'] = response['token']
                context.chat_data['is_admin'] = response['is_admin']

                # Get question data if is the user admin
                if response['is_admin']:
                    response, status = get_with_auth(ApiUrls.ADMIN_QUESTION_ANSWER_GET_DATA.value, response['token'], chat_id=update.effective_chat.id)
                    if status != 200:
                        update.message.reply_text(text='Oops sth went wrong!')
                        return 
                    # if there is no question, create an empty dict
                    if context.bot_data.get('questions_data', None) is None: 
                        context.bot_data['questions_data'] = dict()
                    # set questions info
                    chat_id = update.effective_chat.id
                    context.bot_data['questions_data'][chat_id] = dict()
                    for key,value in response.items():
                        context.bot_data['questions_data'][chat_id][key] = value

        return func(update,context,**kwargs)
    
    return wrapper_func