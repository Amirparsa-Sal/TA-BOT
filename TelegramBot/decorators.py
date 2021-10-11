from request_util import ApiUrls,get

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
            if status != 200:
                update.message.reply_text(text='Oops sth went wrong!')
                return 

            if response['token'] is not None:
                context.user_data['token'] = response['token']
                context.user_data['is_admin'] = response['is_admin']
        return func(update,context,**kwargs)
    
    return wrapper_func