from .Gbot import GeorgeBot, telebot, logger

class AccessMixin:
    def access(self:GeorgeBot, access_lvl:int=0, /, page_type:str=None, shadow=False):
        if page_type != None:
            access_lvl = 8
        def decorator(func):
            def protected(*args, **kwargs):
                message: telebot.types.Message|telebot.types.CallbackQuery
                message = args[0]
                user = self.get_user(message)
                # status_list = ["unknow", "banned", "newcomer", "simple", "premium", "master", "admin", "foreman", "god"]
                status = user.get("status")
                match status:
                    case "unknow" | "banned":
                        lvl = -1
                    case "newcomer":
                        lvl = 0
                    case "simple":
                        lvl = 1
                    case "premium":
                        lvl = 4
                    case "master":
                        lvl = 5
                    case "admin" | "foreman":
                        lvl = 8
                    case "god":
                        lvl = 100
                    case _:
                        return
                denied = False
                kwargs.update({'user': user})
                if lvl >= access_lvl:
                    return func(*args, **kwargs)
                match type(message):
                    case telebot.types.Message:
                        text = message.text
                        sep = ' '
                    case telebot.types.CallbackQuery:
                        text = message.data
                        sep = '#'
                if page_type is not None:
                    try:
                        page_id = text.split('#')[1]
                    except:
                        logger.error("Access technical denial: no page id")
                    try:
                        ID = user.get('id')
                    except:
                        logger.error("Access technical denial: no user id")
                    match page_type:
                        case "show_order":
                            order = self.orders_data.fetch(page_id)
                            if ID in (order.get('master'), order.get('customer')):
                                return func(*args, **kwargs)
                        case "edit_order":
                            order = self.orders_data.fetch(page_id)
                            if ID == order.get('customer'):
                                return func(*args, **kwargs)
                        case "perform_order":
                            order = self.orders_data.fetch(page_id)
                            if ID == order.get('master'):
                                return func(*args, **kwargs)
                if shadow:
                    return
                self.display(user, "access_denial")
            return protected
        return decorator
