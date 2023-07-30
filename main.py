from Gbot import GeorgeBot
from base import Base
import telebot
import threading
import sys
import clock
import re
import logging
from schedule import Scheduler
from exceptor import Exceptor
from available_days import available_days
from Gbot import exc
from get_version import get_version
import logging.config
import splitter
import pickle
import json


closed = False
problems = {}
prob_count = 0
CONTENT_TYPES = ["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact",
                 "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
                 "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
                 "migrate_from_chat_id", "pinned_message"]

logger = logging.getLogger(__name__)

class Admin:
    def __init__(self) -> None:
        self.complete = False
        self.s = self.start
        self.c = self.close
        self._get_bot_presets()
        self.auto_restart = False
        self.a_r_deep_limit = -1
        self.a_r_deep_count = 0
        self.exceptor = Exceptor()
        self.users_data = Base('u', self)
        self.orders_data = Base('o', self)
        self.bot = GeorgeBot(getattr(self, "token", ''), self.users_data, self.orders_data)
        self.scheduler = Scheduler(self.bot)
        self.thr_presets = {
            'm': {'target': self.__main, 'args': (self.bot, self.users_data, self.orders_data)},
            's': {'target': self.__schedule, "args": []}
        }
        self.threads = {}
    

    @exc.protect
    def autorestart(self, arg:str=None):
        if arg in {'0', 'false', 'False', 'f', 'F'}:
            self.auto_restart = False
        elif arg in {'1', 'true', 'True', 't', 'T', None}:
            self.auto_restart = True
        else:
            try:
                arg = int(arg)
                self.a_r_deep_limit = arg
                self.auto_restart = bool(arg)
            except:
                logger.info("unknow args")

    @exc.protect
    def ban_profile(self, *args) -> None:
        ID, date, time = (list(args) + [None]*3)[:3]
        term = ' '.join([date, time])
        while not self.users_data.verify(ID):
            ID = input("user ID: ")
        while not clock.get_datetime(term) and term != '~':
            term = input("term(%Y-%M-%D %H-%M-%S): ")
        self._ban_profile(ID, term)
    
    @exc.protect
    def stress_test(self, num=100):
        def _stress_test(num):
            for i in range(num):
                self.scheduler.new_event({"time":clock.now('+5sec'),
                                    "code":f"test.{i}",
                                    "regularity": {'seconds': 5}
                                    })
            clock.wait(4.5)
        self.thr_presets.update({'stress_test': {'target': _stress_test, 'args': [int(num)]}})
        self.start('stress_test')


    @exc.protect
    def close(self, *threads) -> None:
        logger.info("closing process:")
        if not threads or threads == 'all':
            threads = self.threads.copy()
            self.complete = True
        for thr in threads:
            logger.info(f"|\tthread {thr}:")
            try:
                match thr:
                    case 'm':
                        self.bot.stop_bot()
                        del self.bot
                    case 's':
                        self.scheduler.close()
                        del self.scheduler
                thread: threading.Thread = self.threads.get(thr)
                thread.join()
                self.threads.pop(thr)
                logger.info('|\t|\tclosed.')
            except Exception as e:
                logger.error(f"|\t|\tsome problem during closing thread {thr}: {e}")
                exc.tracebacking()
                global prob_count
                prob_count += 1
                self.complete = False
        if self.complete and not self.threads:
            global closed
            closed = True
            logger.info("====================== session comleted ======================")

    @exc.protect
    def dir(self):
        var_dict = vars(self)
        def convert(val):
            try: 
                json.dumps(val)
            except:
                val = str(val)
            finally:
                return val
        D = {key: convert(var_dict.get(key)) for key in var_dict.keys()}
        logger.info(json.dumps(D, indent=4))
    

    @exc.protect
    def presets(self, *args) -> dict[str]:
        with open('bot_presets.json', 'rb') as f:
            presets = json.load(f)
        if len(args) == 0:
            logger.info(json.dumps(presets, indent=4))
        return presets
    
    @exc.protect
    def clear_presets(self, *args) -> None:
        self._set_presets({})

    @exc.protect
    def update_presets(self, *args) -> dict[str]:
        if not args:
            return
        b = args[0][0]
        if b != '{':
            logger.error(f"sintactic error: excpected '{'{'}', but {args[0]} given")
            return
        line = ''
        for word in args:
            line += word
        while not '}' in line:
            line += input()
        line = line.replace(' ', '').replace('{', '').replace(',}', '').replace('}', '')
        array = line.split(',')
        presets = self.presets(None)
        for data in array:
            spot = data.find(':')
            key, val = data[:spot], data[spot+1:]
            presets.update({key:val})
        self._set_presets(presets)
    
    @exc.protect
    def set_event(self, mode, *args):
        if args:
            line = ' '.join(args)
            try:
                args = json.loads(line)
            except:
               args = line
        else:
            args = None
        match mode:
            case "new" | "edit":
                while type(args) != dict:
                    args = json.loads(input("Please insert dict: "))
                event_data = args
            case "on" | "off" | "complete" | "del" | 'resume':
                while type(args) != str or not self.scheduler.timetable.verify(args):
                    args = input("Please insert ID of existing event: ")
                event_id = args
            case _:
                return
        match mode:
            case 'edit':
                ID = event_data.pop('id')
                request = event_data
            case "new":
                ID = None
                request = {"event": event_data}
            case _:
                ID = event_id
                request = mode
        self.scheduler.set_event_data(ID, request)

    
    @exc.protect
    def show_data(self, name, mode="table", *args):
        match name:
            case "profiles":
                DATA = self.users_data.show()
            case "orders":
                DATA = self.orders_data.show()
            case "files":
                DATA = self.bot.files_data.show()
            case "events":
                DATA = self.scheduler.timetable.show()
            case _:
                logger.warning("unknow data name")
                return
        match mode:
            case "table":
                logger.info(DATA)
            case "dict":
                logger.info(json.dumps(DATA, indent=4))
            case "file":
                return
            case _:
                logger.info('unknow mode')


    @exc.protect
    def start(self, *threads) -> None:
        if self.complete or closed:
            logger.warning("session completed already")
            return
        if not threads:
            threads = ['m', 's']
        for thr in threads:
            try:
                # if getattr(self, 'bot', None) is None and 'm' in threads or 's' in threads:
                #     self.bot = GeorgeBot(getattr(self, 'token'), self.users_data, self.orders_data)
                if getattr(self, 'scheduler', None) is None and 's' in threads:
                    self.scheduler = Scheduler(self.bot)
                arguments = self.thr_presets.get(thr)
                thread = threading.Thread(target=arguments['target'], args=arguments['args'])
                self.threads.update({thr: thread})
                thread.start()
                logger.info(f"thread {thr} was started")
            except Exception as e:
                logger.info(f"tread {thr} wasn't started: {e}")
                exc.tracebacking()
                global prob_count
                prob_count += 1
    
    @exc.protect
    def _ban_profile(self, ID, term, reason='br-other'):
        user = self.users_data.fetch(ID)
        match user.get('status'):
            case 'god':
                return
            case 'banned':
                now = clock.get_datetime()
                date1, date2 = map(clock.get_datetime, (user.get('unban_date'), term))
                delta1, delta2 = map(lambda x: x - now, (date1, date2))
                delta = delta1 + delta2
                # modifier = 1-(delta.total_seconds() / 13107231)
                # self.bot.set_reputation(modifier=modifier)
                term = clock.get_dateline((now + delta))
            case 'premium':
                return
            case None:
                return
        self.bot.ban(ID, term, reason)
        self.scheduler.new_event({"code":f"unban.{ID}", "time":term})


    @exc.protect
    def _command_exec(self, command) -> True:
        request = command.split()
        if request == []:
            with open("input/request.txt", 'r+') as f:
                request = f.read().split()
                f.truncate()
        com, args = request[0], request[1:]
        func = getattr(self, com, None)
        if func is None or com[:2] == "__":
            logger.info("unknow command")
        elif com[0] == '_':
            logger.info("access error")
        else:
            func(*args)
    
    def _get_bot_presets(self):
        with open('bot_presets.json', 'rb') as f:
            try:
                presets: dict = json.load(f)
            except Exception as e:
                logger.info(e)

        for key, val in presets.items():
            setattr(self, key, val)
    
    def _set_presets(self, presets:dict[str]):
        with open('bot_presets.json', 'wb') as f:
            try:
                json.dump(presets, f)
            except Exception as e:
                logger.warning(e)
                return
        logger.info("bot presets has been edited. to make the changes take effect, make a restart program")
    

    def __schedule(self):
        scheduler = getattr(self, 'scheduler', Scheduler(self.bot))
        scheduler.schedule()

    def __main(self, bot: GeorgeBot, users_data: Base, orders_data: Base):
        @bot.message_handler(commands=["start"])
        def start(message: telebot.types.Message):
            user = message.from_user
            text = users_data.sign_in(user)
            bot.send_message(user.id, text)
        
        @bot.message_handler(commands=['ban'])
        @bot.access(8)
        def ban(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            command, *args = message.text.split() + [None]
            ID = args[0]
            if not self.users_data.verify(ID):
                # reply = message.reply_to_message
                # ID = reply.from_user.id
                ID = message.forward_from_message_id
            if not self.users_data.verify(ID):
                return
            user.update({'ban_target': ID})
            bot.display(user, "ban_menu")
        
        @bot.callback_query_handler(func=lambda call: call.data[:3] == 'ban')
        @bot.access(8)
        def ban_menu(call: telebot.types.CallbackQuery):
            user = bot.get_user(call)
            target_id, br = call.data.split('#')[1:]
            bot.set_nav(f'ban_menu#{target_id}#{br}', user, type(call))
            match br:
                case "abusive_behavior":
                    heavy_list = ['1 hour', '3 hours', '1 day', '4 days', '1 week']
                case "bug_exploits":
                    heavy_list = ['1 week', '3 weeks', '30 days', '360 days', 'permanent']
                case "financial_fraud":
                    heavy_list = ['2 weeks', '5 weeks', '360 days', '720 days', 'permanent']
                case "other":
                    heavy_list = ['30 min', '1 hour', '1 day', '1 week', '30 days']
            menu = telebot.types.InlineKeyboardMarkup()
            for point in heavy_list:
                menu.add(telebot.types.InlineKeyboardButton(point, switch_inline_query_current_chat=point))
            bot.send_message(call.message.chat.id, text='pick or print', reply_markup=menu)
            
        
        @bot.message_handler(commands=['report'])
        @bot.access(2)
        def report(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            command, *args = message.text.split() + [None]
            ID = args[0]
            if not self.users_data.verify(ID):
                # reply = message.reply_to_message
                # ID = reply.from_user.id
                ID = message.forward_from_message_id
            user.update({'ban_target': ID})
            bot.display(user, "report_menu")
        
        @bot.message_handler(commands=['main'])
        def main_menu(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            request = {'nav': 'main_menu'}
            self.users_data.update_profile(user['id'], request)
            user.update(request)
            bot.display(user, 'main_menu')

        @bot.callback_query_handler(func=lambda call: 'enter ' in call.data)
        def enter(call: telebot.types.CallbackQuery):
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            obj = call.data[6:]
            user = bot.get_user(call)
            bot.set_nav(f"enter+{obj.replace(' ', '#')}", user, type(call))
            if not ' ' in obj:
                ID = call.from_user.id
            else:
                obj, ID = obj.split()
            bot.display(user, "enter_description_menu")

        @bot.callback_query_handler(func=lambda call: 'to ' in call.data)
        @bot.access()
        def navigation(call: telebot.types.CallbackQuery):
            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except:
                pass
            path_end = call.data[3:].split('#')
            destination = path_end[0]
            match destination:
                case "calendary":
                    calendary(call)
                case "deadline":
                    deadline(call)
                case "description_of_order":
                    edit_description(call)
                case "file":
                    view_file(call)
                case "reference_of_order":
                    edit_references(call)
                case "settings":
                    settings(call)
                case "profile":
                    profile(call)
                case "main_menu":
                    main_menu(call)
                case "language":
                    language(call)
                case "my_orders":
                    my_orders(call)
                case "new_order":
                    new_order(call)
                case "edit_order":
                    edit_order(call)
                case "reference_deleter":
                    reference_deleter(call)
                case "reference_viewer":
                    reference_viewer(call)
                case "type_of_order":
                    edit_type(call)
                case _:
                    unknow_destination(call)
       

        @bot.callback_query_handler(func=lambda call: call.data[:9] == "calendary")
        def calendary(call: telebot.types.CallbackQuery):
            user:dict = bot.get_user(call)
            date, note = (splitter.split(call.data, '#')+['', None])[1:3]
            moment = clock.package(date, gradation='standart')
            user.update({"note": note, "msg_id": call.message.id})
            year, month, day = moment.get('year'), moment.get('month'), moment.get('day')
            if year is None:
                user.update({"timeline": range(2023, 2051)})
                bot.display(user, "calendary_years")
                return
            user.update({'year': year})
            if month is None:
                user.update({"timeline": range(13)})
                bot.display(user, "calendary_months")
                return
            if 1 > month > 12:
                return
            user.update({'month': month})
            if day is None:
                user.update({"timeline": available_days(user, note)})
                bot.display(user, "calendary_days")
                return
            days = available_days(user)
            if days[0][0] > int(day) > days[-1][0]:
                return
            user.update({"day": int(day)})
            hour, minute = moment.get('hour'), moment.get('minute')
            hours = bot.available_hours(user)
            if hour is None:
                user.update({"timeline": hours})
                bot.display(user, "calendary_hours")
                return
            if 0 > hour > 23:
                return
            user.update({"hour": hour})
            minutes = bot.available_minutes(user)
            if minute is None:
                user.update({"timeline": minutes})
                bot.display(user, "calendary_minutes")
                return
            if 0 > minute > 60:
                return
            user.update({"minute": minute})
            user.update({'days': days, 'hours': hours, 'minutes': minutes})
            bot.display(user, "calendary_finaly")
        

        @bot.callback_query_handler(func=lambda call: call.data[:9]=='deadline#')
        def deadline(call: telebot.types.CallbackQuery):
            data = call.data.split('#')
            user:dict = bot.get_user(call)
            order_id = data[1]
            date = data[-1]
            if order_id == date:
                bot.set_nav(f"edit_deadline_menu#{order_id}", user, type(call))
            nav = user.get('nav')
            path = nav.split('/')
            path_end = path[-1]
            id_list = list(map(int, re.findall(r'(?<=#)\d*', path_end)))
            if order_id != date:
                self.orders_data.update(order_id, "deadline", date)
                message_id = id_list.pop(-1)
                chat_id = id_list.pop(-1)
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    logger.debug(f'un-suc-ll try to del msg: {chat_id=}, {message_id=}')
            message = bot.display(user, "edit_deadline_menu")
            id_list += [call.message.chat.id, message.id]
            path[-1] = '#'.join(list(map(str, ['edit_deadline_menu']+id_list)))
            nav = '/'.join(path)
            bot.set_nav(nav, user, type(call.message))



        def reference_deleter(call: telebot.types.CallbackQuery):
            data = call.data.split('#')
            user:dict = bot.get_user(call)
            order_id = data[1]
            bot.set_nav(f"reference_deleter#{order_id}", user, type(call))
            bot.display(user, "reference_deleter")
        
        def reference_viewer(call: telebot.types.CallbackQuery):
            data = call.data.split('#')
            user:dict = bot.get_user(call)
            err = False
            order_id = data[1]
            bot.set_nav(f"reference_viewer#{order_id}", user, type(call))
            bot.display(user, "reference_viewer")


        @bot.callback_query_handler(func=lambda call: 'confirm ' in call.data)
        def confirm(call: telebot.types.CallbackQuery):
                try:
                    bot.delete_message(call.message.chat.id, call.message.id)
                except:
                    pass
                user = bot.get_user(call)
                nav = user.get('nav')
                path = nav.split('/')
                end = path[-1]
                by_sharp = end.split('#')
                by_ampersand = end.split('&')
                location = by_sharp[2]
                msg_list = list(map(int, by_sharp[3:-1]))
                for msg_id in msg_list:
                    try:
                        bot.delete_message(call.message.chat.id, msg_id)
                    except:
                        continue
                data = call.data.split()
                match data[1]:
                    case 'del':
                        callback_list = by_ampersand[1:]
                        for callback_data in callback_list:
                            call.data = callback_data
                            delete(call)
                    case 'cancel':
                        pass
                but:telebot.types.InlineKeyboardButton = bot.display(user, 'back')
                call.data = but.callback_data
                navigation(call)

        
        @bot.callback_query_handler(func=lambda call: 'switch ' in call.data)
        def switch(call: telebot.types.CallbackQuery):
            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except:
                pass
            data = call.data.split()
            user:dict = bot.get_user(call)
            err = False
            match data[1]:
                case "sys_lang":
                    request = {
                        "nav": user['nav']+'/swt',
                        "sys_lang": 1, 
                        "language_code": call.data.from_user.language_code
                    }
                case "language":
                    lang = data[-1]
                    request = {"language_code": lang, "nav": user['nav']+'/swt'}
                case _:
                    err = True
                    unknow_destination(call)
            if not err:
                users_data.update_profile(user['id'], request)
                user.update(request)
                bot.display(user, "switch")
        
        @bot.callback_query_handler(func=lambda call: 'del ' in call.data)
        def delete(call: telebot.types.CallbackQuery):
            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except:
                pass
            data = call.data.split()
            user:dict = bot.get_user(call)
            err = False
            match data[1]:
                case "profile":
                    request = {
                        "nav": user['nav']+'/del_profile',
                    }
                    users_data.update_profile(user['id'], request)
                    user.update(request)
                    bot.display(user, "confirm_del_profile")
                case "description":
                    order_id = data[2]
                    request = {"description": ""}
                    orders_data.update_order(order_id, request)
                    bot.display(user, "edit_description_menu")
                case "file" | "files":
                    order_id = data[2]
                    loc = data[3]
                    file_id = data[4]
                    order = orders_data.fetch(order_id)
                    location = {'r': 'reference', 'p': 'product', 'd': 'documentation'}.get(loc)
                    folder:dict = order.get(location)
                    file:dict = folder.pop(file_id)
                    bot.files_data.delete(file_id)
                    orders_data.update_order(order_id, {location: json.dumps(folder).encode('utf-8')})
                    call.data = bot.display(user, "back").callback_data
                    if data[1] == 'file':
                        navigation(call)
                case "sr":  
                    nav = user.get('nav')
                    order_id = nav.split('/')[-1].split('#')[1]
                    order = orders_data.fetch(order_id)
                    folder = order.get('reference', {})
                    select_code = int(data[-1])
                    l = len(folder)
                    selected = ('0'*l+bin(select_code)[2:])[-l:]
                    msg_list = ''
                    callback_list = ''
                    chat_id = call.message.chat.id
                    for i, item in enumerate(sorted(folder.items())):
                        match selected[i]:
                            case '0':
                                continue
                            case '1':
                                f_id, f_info = item
                                file_info = bot.document_upload(f_info, f_id)
                                msg:telebot.types.Message = bot.send_document(chat_id, **file_info)
                                msg_list+= f"#{msg.id}"
                                callback_list += '&' + f"del files {order_id} r {f_id}"
                    nav = f"confirm_del_file#{order_id}#{'reference'}{msg_list}#{callback_list}"
                    bot.set_nav(nav, user, type(call))
                    bot.display(user, "confirm_del_files")
                                
                    
                case _:
                    err = True
                    unknow_destination(call)
        
        @bot.callback_query_handler(func=lambda call: 's|' in call.data)
        def select(call:telebot.types.CallbackQuery):
            data = call.data.split('|')
            select_list = {'rd': "reference_deleter"}
            loc = data[1]
            location = select_list.get(loc)
            select_code = int(data[-1])
            user:dict = bot.get_user(call)
            user.update({'selected': select_code, "msg_id": call.message.id})
            bot.display(user, location)
        
        @bot.callback_query_handler(func=lambda call: call.data == "x")
        def pass_out(call):
            pass
        
        def unknow_destination(message: telebot.types.CallbackQuery):
            user = bot.get_user(message)
            if user is None:
                bot.send_message(message.from_user.id, "Unknow user id error. Maybe profile has been deleted, please press or write /start to LOG IN")
                return
            user = bot.set_nav("unknw_des", user, type(message))
            bot.display(user, "unknw_des")
        
        @bot.message_handler(commands=['file'])
        def view_file(message: telebot.types.CallbackQuery|telebot.types.Message):
            user = bot.get_user(message)
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            data = text.split(sep)
            order_id, loc, f_id = (data[1:4] + [None]*3)[:3]
            user = bot.set_nav(f"file#{order_id}", user, type(message))
            location = {'r': 'reference', 'p': 'product', 'd': "documentation"}.get(loc)
            user.update({'f_id': str(f_id), 'f_loc': str(location)})
            bot.display(user, "view_file")
        
        @bot.message_handler(commands=['new'])
        @bot.access()
        def my_orders(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            user = bot.set_nav(f"my_orders", user, type(message))
            bot.display(user, "my_orders_menu")
        
        @bot.message_handler(commands=['description'])
        @bot.access()
        def edit_description(message: telebot.types.Message|telebot.types.CallbackQuery):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = bot.get_user(message)
            order_id = text.split(sep)[-1]
            order = self.orders_data.fetch(order_id)
            if order.get('status', None) == 'created':
                user = bot.set_nav(f"description_of_order#{order_id}", user, type(message))
                bot.display(user, "edit_description_menu")
            else:
                user = bot.set_nav(f"show_order#{order_id}", user, type(message))
                bot.display(user, "show_order_menu")

        @bot.message_handler(commands=['new'])
        @bot.access()
        def new_order(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            order_id = bot.new_order(user)
            user = bot.set_nav(f"edit_order#{order_id}", user, type(message))
            bot.display(user, "edit_order_menu")
        
        @bot.message_handler(commands=['edit'])
        @bot.access(page_type='edit_order')
        def edit_order(message: telebot.types.Message|telebot.types.CallbackQuery):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = bot.get_user(message)
            order_id = text.split(sep)[-1]
            order = self.orders_data.fetch(order_id)
            if order.get('status', None) == 'created':
                user = bot.set_nav(f"edit_order#{order_id}", user, type(message))
                bot.display(user, "edit_order_menu")
            else:
                user = bot.set_nav(f"show_order#{order_id}", user, type(message))
                bot.display(user, "show_order_menu")
        
        @bot.message_handler(commands=['references'])
        @bot.access()
        def edit_references(message: telebot.types.Message|telebot.types.CallbackQuery):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = bot.get_user(message)
            order_id = text.split(sep)[-1]
            order = self.orders_data.fetch(order_id)
            user = bot.set_nav(f"reference_of_order#{order_id}", user, type(message))
            bot.display(user, "edit_reference_menu")
        
        @bot.message_handler(commands=['type'])
        @bot.access()
        def edit_type(message: telebot.types.Message|telebot.types.CallbackQuery):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = bot.get_user(message)
            order_id = text.split(sep)[-1]
            order = self.orders_data.fetch(order_id)
            if order.get('status', None) == 'created':
                user = bot.set_nav(f"type_of_order#{order_id}", user, type(message))
                bot.display(user, "edit_type_menu")
            else:
                user = bot.set_nav(f"show_order#{order_id}", user, type(message))
                bot.display(user, "show_order_menu")

        @bot.message_handler(commands=['settings'])
        def settings(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            user = bot.set_nav("settings", user, type(message))
            bot.display(user, "settings_menu")
        
        @bot.message_handler(commands=['profile'])
        def profile(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            user = bot.set_nav('profile', user, type(message))
            bot.display(user, 'profile_menu')
        
        @bot.message_handler(commands=['language'])
        def language(message: telebot.types.Message|telebot.types.CallbackQuery):
            user = bot.get_user(message)
            user = bot.set_nav("language", user, type(message))
            bot.display(user, "language_menu")
        
        @bot.callback_query_handler(func=lambda call: call.data=='X')
        def invalid_date(call: telebot.types.CallbackQuery):
            user = bot.get_user(call)
            text = bot.display(user, "invalid_date")
            bot.answer_callback_query(call.id, show_alert=True, text=text)
        
        @bot.message_handler(content_types=CONTENT_TYPES)
        def content_handler(message: telebot.types.Message):
            user:dict = bot.get_user(message)
            if user is None:
                bot.send_message(message.from_user.id, "Unknow user id error. Maybe profile has been deleted, please press or write /start to LOG IN")
                return
            path = user['nav'].split('/')
            path_end = path[-1]
            match message.content_type:
                case "text":
                    result = bot.text_handler(message, user, path_end)
                case "document" | "audio":
                    bot.document_handler(message, user, path_end)
                case _:
                    pass
            if result is not None:
                com, trg, term, desc = (result + [None]*4)[:4]
                match com:
                    case 'ban':
                        self._ban_profile(trg, term, desc)
                        bot.send_message(user.get('id'), 'user banned')
        try:
            logger.debug("polling right now")
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            logger.error(f'bot polling will stoped by Fatal Error: \n\t{e}')
            exc.tracebacking()
            logger.warning('need a restart')
            try:
                bot.fatal_warning()
            except Exception as ee:
                logger.info(f'Fatal warning send error:\n\t{ee}')
            if self.auto_restart and self.a_r_deep_count != self.a_r_deep_limit:
                self.a_r_deep_count += 1
                try:
                    self.start()
                    logger.warning(f"main thread was restarted. restarts left: {self.a_r_deep_limit - self.a_r_deep_count}")
                except Exception as ee:
                    logger.critical(f"Fatal autorestart error:\n\t{ee}")
            else:
                logger.warning(f"restarts left: {self.a_r_deep_limit - self.a_r_deep_count}")


if __name__ == "__main__":
    # logger = get_log_config()
    # logging.basicConfig(format="%(asctime)s %(levelname)s:%(name)s:%(lineno)s> %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
    from set_logging import config
    config()
    ver = get_version()
    logger.info(f"{f'{ver:10s}'.replace(' ', '=')}============ session started =======================")
    admin = Admin()
    for command in sys.stdin:
        admin._command_exec(command)
        if closed:
            break
