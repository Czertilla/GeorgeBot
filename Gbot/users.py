from .Gbot import GeorgeBot, telebot, uknw, exc

class UsersMixin:
    @uknw
    @exc.protect
    def get_user(self:GeorgeBot, message: telebot.types.Message|telebot.types.CallbackQuery) -> dict:
        ID = message.from_user.id
        user = self.users_data.fetch(ID)
        if bool(user.get('sys_lang')):
            lang = message.from_user.language_code
            if lang != user['language_code']:
                self.users_data.update_profile(ID, request={'language_code': lang})
                user.update({'language_code':lang})
        return user    

    def set_nav(self:GeorgeBot, loc: str, user: dict, message_type: type) -> dict:
        match message_type:
            case telebot.types.Message:
                nav = loc
            case telebot.types.CallbackQuery:
                nav = user.get('nav', 'main_menu')
                if loc in nav: 
                    nav = nav[:nav.find(loc)+len(loc)]
                else:
                    nav += f'/{loc}'
        request = {'nav': nav}
        self.users_data.update_profile(user['id'], request)
        user.update(request)
        return user

    @exc.protect
    def set_msg_to_del(self:GeorgeBot, user:dict, message:telebot.types.Message) -> None:
        nav:str = user.get('nav')
        path = nav.split('/')
        location:str = path[-1]
        loc, order_id, chat_id, msg_id = location.split('#')[:2]+[message.chat.id, message.id]
        nav = nav.replace(location, '') + f'{loc}#{order_id}#{chat_id}#{msg_id}'
        self.set_nav(nav, user, type(message))
