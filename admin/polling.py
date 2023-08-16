from .admin import Admin, logger
from Gbot import GeorgeBot
from base import Profiles, Orders
from constants import *
import telebot
import tools.clock as clock
import re
from tools.available_days import available_days
from Gbot import exc
import tools.splitter as splitter
import json

class PollingMixin:
    def _main(self:Admin, bot: GeorgeBot, users_data: Profiles, orders_data: Orders):
        @bot.message_handler(commands=["start"])
        def start(message: telebot.types.Message):
            user = message.from_user
            text = users_data.sign_in(user)
            bot.send_message(user.id, text)

        @bot.message_handler(commands=['ban'])
        @bot.access(8)
        def ban(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            user = kwargs.get('user', bot.get_user(message))
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
        def ban_menu(call: telebot.types.CallbackQuery, **kwargs):
            user = kwargs.get('user', bot.get_user(call))
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
        def report(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            user = kwargs.get('user', bot.get_user(message))
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
        def navigation(call: telebot.types.CallbackQuery, **kwargs):
            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            except:
                exc.tracebacking()
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
                self.orders_data._update(order_id, "deadline", date)
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
                case "type":
                    order_type, order_id = data[2].split('#')
                    request = {
                        "type": order_type
                    }
                case "sys_lang":
                    request = {
                        "nav": user['nav']+'/swt',
                        "sys_lang": 1, 
                        "language_code": call.from_user.language_code
                    }
                case "language":
                    lang = data[-1]
                    request = {"language_code": lang, "nav": user['nav']+'/swt', "sys_lang": 0}
                case _:
                    err = True
                    unknow_destination(call)
            if not err:
                match data[1]:
                    case "sys_lang"|"language":
                        users_data.update_profile(user['id'], request)
                        user.update(request)
                        bot.display(user, "switch")
                    case "type":
                        orders_data.update_order(int(order_id), request)
                        bot.display(user, "edit_type_menu")
        
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
                case 'order':
                    order_id = data[2]
                    if data[-1] != order_id:
                        orders_data.delete(int(order_id))
                        call.data = bot.display(user, "back").callback_data
                        navigation(call)
                    else:
                        bot.display(user, "confirm_del_order")
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
            select_list = {'rd': "reference_deleter", 'mo': "my_orders_menu", 'mp': "my_projects_menu"}
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
        def my_orders(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            user = kwargs.get('user', bot.get_user(message))
            user = bot.set_nav(f"my_orders", user, type(message))
            bot.display(user, "my_orders_menu")
        
        @bot.message_handler(commands=['description'])
        @bot.access()
        def edit_description(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = kwargs.get('user', bot.get_user(message))
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
        def new_order(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            user = kwargs.get('user', bot.get_user(message))
            order_id = bot.new_order(user)
            match order_id:
                case "too many":
                    user = bot.set_nav("too_many", user, type(message))
                    code = "too_many_orders"
                case "banned":
                    user = bot.set_nav("banned", user, type(message))
                    code = "banned"
                case _:
                    user = bot.set_nav(f"edit_order#{order_id}", user, type(message))
                    code = "edit_order_menu"
            bot.display(user, code)

        @bot.message_handler(commands=['edit'])
        @bot.access(page_type='edit_order')
        def edit_order(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = kwargs.get('user', bot.get_user(message))
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
        def edit_references(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = kwargs.get('user', bot.get_user(message))
            order_id = text.split(sep)[-1]
            order = self.orders_data.fetch(order_id)
            user = bot.set_nav(f"reference_of_order#{order_id}", user, type(message))
            bot.display(user, "edit_reference_menu")
        
        @bot.message_handler(commands=['type'])
        @bot.access()
        def edit_type(message: telebot.types.Message|telebot.types.CallbackQuery, **kwargs):
            match type(message):
                case telebot.types.Message:
                    sep = ' '
                    text = message.text
                case telebot.types.CallbackQuery:
                    sep = '#'
                    text = message.data
            user = kwargs.get('user', bot.get_user(message))
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
            bot.download_buffer.update(message.chat.id)
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
                    return
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
