import logging
import telebot
from base import getBase, Profiles, Orders, Files 
from exceptor import Exceptor
from phrases import tell
from phrases import language_codes
from try_int import try_int
from Gbot.meta import MetaBot
import clock
import json
import re

logger = logging.getLogger(__name__)
exc = Exceptor()

from Gbot.unknw import uknw

class GeorgeBot(telebot.TeleBot, metaclass=MetaBot):
    def __init__(self, token, u_d:Profiles, o_d:Orders):
        telebot.TeleBot.__init__(self, token, num_threads=50)
        files_data:Files = getBase("Files")
        self.download_buffer = Buffer()
        self.files_data = files_data
        self.users_data = u_d
        self.orders_data = o_d
        self.months = ['month', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        self.weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

    def access(self, access_lvl:int=0, /, page_type:str=None, shadow=False):
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

    def available_hours(self, user:dict) -> list:
        note = user.get("note")
        match note:
            case "deadline":
                year, month, day = [user.get(key) for key in ('year', 'month', 'day')]
                limit = clock.now('+1hour')
                answer = []
                for h in range(24):
                    if f"{year}-{month:02}-{day:02} {h:02}:59:59" > limit:
                        answer.append(h)
                return answer
            case _:
                return [h for h in range(24)]
    
    def available_minutes(self, user:dict) -> list:
        note = user.get("note")
        match note:
            case "deadline":
                year, month, day, hour = [user.get(key) for key in ('year', 'month', 'day', 'hour')]
                limit = clock.now('+1hour')
                answer = []
                for m in range(60):
                    if f"{year}-{month:02}-{day:02} {hour:02}:{m:02}:59" > limit:
                        answer.append(m)
                return answer
            case _:
                return [m for m in range(60)]
    
    @exc.protect
    def current_switch(self, user:dict, code:str) -> str:
        match code:
            case "language_menu":
                if user["sys_lang"]:
                    return "system_language"
                return "language_codes"

    def document_download(self, message: telebot.types.Message, user:dict, folder_path) -> tuple[str, dict]:
        try:
            document:telebot.types.Document = getattr(message, "document", None)
            audio: telebot.types.Audio = getattr(message, "audio", None)
            if document is None:
                document = audio
            file_info = self.get_file(document.file_id)
            file_bytes = self.download_file(file_info.file_path)
            file = {
                'tg_id': document.file_id,
                'name': document.file_name,
                'folder': folder_path,
                'bytes': file_bytes,
            }
            ID = self.files_data.download_file(file)
            if ID is None:
                raise Exception("File doesn`t downloaded")
            user.update({"file_name": file.get('name')})
            self.display(user, "good_file")
            return file_info
        except Exception as e:
            self.edit_message_text(e, user.get('load_cht_id'), user.get('load_msg_id'))
        finally:
            # self.delete_message(user.get('load_cht_id'), user.get('load_msg_id'))
            self.download_buffer.remove(user.get('load_cht_id'))

    def document_upload(self, file_info:dict, f_id) -> str|bytes:
        try:
            tg_id = file_info.get('tg_id')
            file_info = self.get_file(tg_id)
            return {'document': tg_id}
        except:
            f_name = file_info.get('f_name')
            file = self.files_data.upload_file(f_id)
            return {'document': file, 'visible_file_name': f_name}
    
    @exc.protect
    def get_orders(self, /, customer:dict=None, master:dict=None)->dict:
        if customer is not None:
            c_id = customer.get('id')
            cust_orders = self.orders_data.search(c_id, ('customer',)).get('whole')['']
            id_set = set(cust_orders)
        if master is not None:
            m_id = master.get('id')
            mast_orders = self.orders_data.search(c_id, ('master',)).get('whole')['']
            id_set = set(mast_orders)
        if master and customer:
            id_set = set(cust_orders) & set(mast_orders)
        id_dict = {}
        for stat in self.orders_data.status_list:
            id_dict.update({stat: self.orders_data.search(stat, ('status',)).get('whole')['']})
        id_dict.update({"drafts": id_dict.pop('created') + id_dict.pop('recreated')})
        id_dict.update({"archive": id_dict.pop('closed')+id_dict.pop('completed')})
        for stat, id_list in id_dict.items():
            id_dict.update({stat: sorted(id_set & set(id_list), 
                                         key=lambda x: self.orders_data.peek(x, '_status_updated'),
                                         reverse=True)})
        return id_dict


    
    @exc.protect
    def get_services(self)->dict:
        with open("services.json", 'rb') as f:
            return json.load(f)

    @exc.protect
    def set_msg_to_del(self, user:dict, message:telebot.types.Message) -> None:
        nav:str = user.get('nav')
        path = nav.split('/')
        location:str = path[-1]
        loc, order_id, chat_id, msg_id = location.split('#')[:2]+[message.chat.id, message.id]
        nav = nav.replace(location, '') + f'{loc}#{order_id}#{chat_id}#{msg_id}'
        self.set_nav(nav, user, type(message))


    def document_handler(self, message:telebot.types.Message, user:dict, path_end:str) -> None:
        loc, order_id, chat_id, msg_id = (path_end.split('#') + [None]*3)[:4]
        msg = self.reply_to(message, tell("downloading", user.get('language_code')))
        load_cht_id, load_msg_id = msg.chat.id, msg.id
        user.update({'load_cht_id': load_cht_id, 'load_msg_id': load_msg_id})
        match loc:
            case "reference_of_order":
                self.document_download(message,user, f"{order_id}/reference")
                display_code = "edit_reference_menu"
            case _:
                return
        if self.download_buffer.get(message.chat.id) <= 0:
            try:
                self.delete_message(chat_id, msg_id)
                self.display(user, display_code)
                logger.debug("FINAL")
            except:
                pass


    def text_handler(self, message:telebot.types.Message, user: dict, path_end: str):
        if path_end == 'del_profile' and message.text == str(user['id']):
            logger.info(f"{self.users_data.discard_profile(user['id'])}")
            del user
            del message
            return
        id_list = list(map(try_int, re.findall(r'(?<=#)\d*', path_end)))
        location = (re.findall(r'^[^#]*(?=#)', path_end)+[None])[0]
        if location is None:
            return
        match location:
            case 'ban_menu':
                target_id, br = path_end.split('#')[1:]
                ID = int(target_id)
                text = re.sub(r'@[^ ]*(?= )', '+', message.text)
                if not '+' in text:
                    text = '+' + text
                if clock._modify(None, text) is None:
                    return
                self.set_nav('main_menu', user, type(message))
                term = clock.now(text)
                return ['ban', ID, term, br]
            case 'edit_deadline_menu':
                order_id = id_list[0]
                if order_id is None:
                    return
                deadline = clock.package(message.text, gradation='normal', ignore_nulls=True)
                now = clock.now(dict_like=True)
                keys = ("year", "month", "day", "hour", "minute")
                year, month, day, hour, minute, second = [deadline.get(key, 99) for key in keys] + [99]
                flag = False
                if year == 99 and day != 99 and month != 99:
                    year = now.get('year')
                    flag = True
                    dl = f"{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"
                    if clock.now('+1h') > dl:
                        dl = f"{year+1:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"
                else: 
                    dl = f"{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"
                if dl < clock.now('+1hour'):
                    return
                request = {"deadline": dl}
                lang = user.get('language_code')
                chat_id, msg_id = (id_list[-2:] + [None]*2)[:2]
                self.orders_data.update_order(order_id, request)
                try:
                    self.delete_message(chat_id, msg_id)
                    message = self.display(user, "edit_deadline_menu")
                    nav:str = user.get('nav')
                    sharp_list = nav.split('#')
                    nav = '#'.join(sharp_list[:-2]+[f"{message.chat.id}", f"{message.id}"])
                    self.set_nav(nav, user, type(message))
                except:
                    logger.warning(f"set date witout edit message text ({chat_id=}, {msg_id=})")
                    exc.tracebacking()
                return
            case 'enter+description':
                splited = path_end.split('+')
                ent = splited[0]
                obj = splited[-1]
                if ent != 'enter':
                    return
                if '#' in obj:
                    obj, ID, chat_id, message_id = obj.split('#')
                else:
                    ID = user['id']
                    chat_id = message.chat.id
                    message_id = message.id - 1
                match obj:
                    case "description":
                        request = {'description': message.text[:3500]}
                        func = self.orders_data.update_order
        func(ID, request)
        self.delete_message(chat_id, message_id)
        self.display(user, 'switch')
    

    @exc.protect
    def ban(self, ID, date:str='~', ban_reason='br-other'):
        user = self.users_data.fetch(ID)
        lang = user.get('lang')
        request = {"status": "banned", "_unban_date": date}
        if date == '~':
            date = tell("pemanent", lang)
        self.users_data.update_profile(ID, request)
        self.send_message(ID, tell("ban_notification", inset={'reason': tell(ban_reason, lang), 'date': date}))
    
    @exc.protect
    def unban(self, ID):
        user = self.users_data.fetch(ID)
        lang = user.get('lang')
        request = {'status': 'simple', '_unban_date': None}
        self.users_data.update_profile(ID, request)
        self.send_message(user.get('id'),tell("unban_notification"))

    @exc.protect
    def spam(self, text, parse_mode):
        for ID in self.users_data.search():
            user = self.users_data.fetch(ID)
            if user.get('status') != 'god':
                continue
            self.send_message(ID, text, parse_mode)


    @exc.protect
    def fatal_warning(self):
        personal = self.users_data.search("god", sample=('status',), only_whole=True)['whole']['']
        for ID in personal:
            self.send_message(ID, "Я упал, подними меня!")
            self.send_message(627784637, "Я упал, подними меня!")


    @exc.protect
    def send_fielde(self, user:dict, obj:str, ID, repl=None):
        lang = user['language_code']
        match obj:
            case "description":
                order_id = ID
                order = self.orders_data.fetch(order_id)
                obj = tell("description_of_order", lang, {"curr": f'<code>{order["description"]}</code>'})
        msg = self.send_message(user['id'], tell("enter_fielde", lang, {'obj': obj}), reply_markup=repl, parse_mode="HTML")
        nav = user['nav'] + f"#{msg.chat.id}#{msg.id}"
        self.set_nav(nav, user, telebot.types.Message)


    @uknw
    @exc.protect
    def get_user(self, message: telebot.types.Message|telebot.types.CallbackQuery) -> dict:
        ID = message.from_user.id
        user = self.users_data.fetch(ID)
        if bool(user.get('sys_lang')):
            lang = message.from_user.language_code
            if lang != user['language_code']:
                self.users_data.update_profile(ID, request={'language_code': lang})
                user.update({'language_code':lang})
        return user    


    @exc.protect
    def new_order(self, user:dict) -> int:
        ID = user['id']
        order_id = self.orders_data.new_order(user)
        match user['status']:
            case 'banned':
                return "banned"
            case 'newcomer':
                request = {'status': 'simple'}
                self.users_data.update_profile(ID, request)
        return order_id


    @exc.protect
    def ready_to_distribute(self, order_id:int, lang:str) -> tuple[str]:
        order = self.orders_data.fetch(order_id)
        ready = 'order_is_ready'
        columns = ''
        if not order.get('type'):
            ready = 'order_not_ready'
            t = tell('type_of_order', lang, ignore_all_insets=True)[:-2]
            columns += t+'\n'
        if not order.get('description'):
            ready = 'order_not_ready'
            t = tell('description_of_order', lang, ignore_all_insets=True)[:-2]
            columns += t+'\n'
        if clock.now('+1hour') >= order.get('deadline', '~'):
            ready = 'order_not_ready'
            t = tell('deadline_of_order', lang,  ignore_all_insets=True)[:-2]
            columns += t+'\n'
        return ready, columns


    def set_nav(self, loc: str, user: dict, message_type: type) -> dict:
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

    def get_command(self, message: telebot.types.Message):
        match type(message):
            case type(''):
                text = message
            case telebot.types.Message:
                text = message.text
        sintax = text.split()
        com, args = sintax[0], sintax[1:]

class Buffer(dict):
    def remove(self, chat_id):
        dict.update(self, {chat_id: self.get(chat_id, 0)-1})
        logger.debug(f'{self.get(chat_id)}(-1)')

    def update(self, chat_id):
        dict.update(self, {chat_id: self.get(chat_id, 0)+1})
        logger.debug(f'{self.get(chat_id)}(+1)')

if __name__ == "__main__":
    GeorgeBot("1", Profiles(), Orders())