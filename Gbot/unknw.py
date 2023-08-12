from .Gbot import telebot

def uknw(func):
    def protected(*args, **kwargs):
        flag = False
        f:dict = func(*args, **kwargs)
        if f['id'] is None:
            message:telebot.types.Message = args[1]
            f.update({
                'id': message.from_user.id,
                'language_code': message.from_user.language_code,
                'status': 'unknow'
            })
        return f
    return protected
