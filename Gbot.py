import logging
import telebot
from base import Base
from exceptor import Exceptor
from phrases import tell
from phrases import language_codes
from try_int import try_int
import clock
import json
import re

logger = logging.getLogger(__name__)
exc = Exceptor()

def uknw(func):
    def protected(*args, **kwargs):
        flag = False
        f = func(*args, **kwargs)
        if f['id'] is None:
            message:telebot.types.Message = args[1]
            f.update({
                'id': message.from_user.id,
                'language_code': message.from_user.language_code,
                'status': 'unknow'
            })
        return f
    return protected




class GeorgeBot(telebot.TeleBot):
    def __init__(self, token, u_d, o_d):
        telebot.TeleBot.__init__(self, token)
        self.files_data = Base('f')
        self.users_data: Base = u_d
        self.orders_data: Base = o_d
        self.months = ['month', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        self.weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

    def access(self, func: "function", access_lvl:int=0) -> "function":
        def protected(*args, **kwargs):
            message = args[0]
            user = self.get_user(message)
            status_list = ["banned","newcomer", "simple", "premium", "master", "foreman", "god"]
            status = user["status"]
            if status in status_list:
                if status_list.index(status) <= access_lvl:
                    self.display(user, "access_denial")
                else:
                    return func(*args, **kwargs)
            elif access_lvl == 0:
                return func(*args, **kwargs)   
        return protected

    def available_hours(self, user:dict) -> list:
        note = user.get("note")
        match note:
            case _:
                return [h for h in range(24)]
    
    def available_minutes(self, user:dict) -> list:
        note = user.get("note")
        match note:
            case _:
                return [h for h in range(24)]


    @exc.protect
    def display(self, user: dict, code: str) -> None|telebot.types.InlineKeyboardButton|telebot.types.Message:
        1/0
        button = telebot.types.InlineKeyboardButton
        menu = telebot.types.InlineKeyboardMarkup()
        ID = user.get('id')
        lang = user.get('language_code', 'en')
        if user['status'] == "unknow":
            self.send_message(ID, tell('unknow_user', lang), parse_mode="HTML")
        nav = user.get('nav')
        path = nav.split('/')
        end:str = path[-1]
        if "#" in end:
            order_id = end.split('#')[1]
            order = self.orders_data.fetch(order_id)
            if "calendary" in code:
                order.update({'deadline': clock.package(order.get('deadline'))})
                note = user.get('note')
                selected:dict = order.get(note, {})
        match code:
            case "access_denial":
                menu.add(self.display(user, 'back'))
                menu.add(self.display(user, 'back_to_home'))
                self.send_message(ID, tell("access_denial", lang, {'status': user['status']}), reply_markup=menu, parse_mode="HTML")
            case "calendary_years":
                windth = 8
                timeline = user.get('timeline')
                l = len(timeline)
                while l % windth:
                    windth -= 1
                menu = telebot.types.InlineKeyboardMarkup(row_width=windth)
                menu.add(*[button(text=year, callback_data=f"calendary#{year}#{note}") for year in timeline])
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except Exception as e:
                    self.send_message(ID, f"{timeline[0]}-{timeline[-1]}", reply_markup=menu)
            case "calendary_months":
                menu = telebot.types.InlineKeyboardMarkup(row_width=4)
                year = user.get("year")
                menu.add(*[
                    button(text=f'<<', callback_data=f"calendary#{year-1}#{note}"),
                    button(text=f"{year}", callback_data=f"calendary##{note}"),
                    button(text=f'>>', callback_data=f"calendary#{year+1}#{note}")
                ])
                menu.add(*[button(tell(self.months[month], lang), callback_data=f"calendary#{year}-{month}#{note}") \
                           for month in range(1, 13)])
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "calendary_days":
                menu = telebot.types.InlineKeyboardMarkup(row_width=7)
                year, month = user.get("year"), user.get('month')
                menu.add(button(f"{year}", callback_data=f"calendary##{note}"))
                topbar = []
                now:dict = clock.now(dict_like=True)
                iterable = (year, month)
                for i, I in enumerate(('year', 'month')):
                    if selected.get(I) != iterable[i]:
                        selected.update({"day": None})
                        break
                for i, I in enumerate(('year', 'month')):
                    if now.get(I) != iterable[i]:
                        now = None
                        break
                else:
                    now = now.get('day')
                if month == 1:
                    topbar.append(button((f"{tell('dec', lang)[:3]},{year-1}<<"), callback_data=f"calendary#{year-1}-12#{note}"))
                else:
                    topbar.append(button(f"{tell(self.months[month-1], lang)}<<", callback_data=f"calendary#{year}-{month-1}#{note}"))
                topbar.append(button(tell(self.months[month], lang), callback_data=f"calendary#{year}#{note}"))
                if month == 12:
                   topbar.append(button((f"{tell('jan', lang)[:3]},{year+1}>>"), callback_data=f"calendary#{year+1}-1#{note}"))
                else:
                    topbar.append(button(f">>{tell(self.months[month+1], lang)}", callback_data=f"calendary#{year}-{month+1}#{note}")) 
                menu.add(*topbar)
                menu.add(*[button(wd, callback_data=wd) for wd in self.weekdays])
                weekday = 0
                timeline:list = user.get('timeline')
                row = []
                while timeline:
                    if weekday >= 7:
                        menu.add(*row)
                        row = []
                        weekday = 0
                    if timeline[0][1] == weekday:
                        day = timeline.pop(0)[0]
                        if day == 0:
                            row.append(button(text='X', callback_data='X'))
                            weekday += 1
                            continue
                        dig_day = day
                        if dig_day == now:
                            day = f':{day}:'
                        if dig_day == selected.get("day"):
                            day = f"\\{day}/"
                        row.append(button(day, callback_data=f"calendary#{year}-{month}#{note}"))
                        # row.append(button(day, callback_data=f"calendary#{year}-{month}-{day}"))
                    else:
                        row.append(button(text='<', callback_data=topbar[0].callback_data))
                    weekday += 1
                if 0 < weekday < 7:
                    row += [button(text='>', callback_data=topbar[-1].callback_data)]*(7-weekday) 
                menu.add(*row)
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "confirm_del_files":
                menu.add(button(tell("cancel_deletion", lang), callback_data="confirm cancel"))
                menu.add(button(tell("confirm_deletion", lang), callback_data="confirm del"))
                self.send_message(ID, tell("confirm_deletion_files", lang), reply_markup=menu)
            case "confirm_del_profile":
                menu.add(self.display(user, 'back'))
                menu.add(self.display(user, 'back_to_home'))
                self.send_message(ID, tell("del_profile_warning", lang, {'id': user['id']}), reply_markup=menu, parse_mode="HTML")
            case "edit_deadline_menu":
                deadline_text = order.get('deadline')
                deadline_form = re.sub(r'.99', '', deadline_text)
                order.update({'deadline': clock.package(deadline_form, ignore_nulls=True)})
                deadline:dict = order.get("deadline", {})
                now:dict = clock.now(dict_like=True)
                keys = ('year', 'month', 'day', 'hour', 'minute')
                date_list = [deadline.get(key, now.get(key)) for key in keys]
                year, month, day, hour, min = date_list
                menu.add(button(tell("select_date", lang), callback_data=f"calendary#{year}-{month}#deadline"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                template = {'year': tell('year_temp', lang),
                            'month': tell('month_temp', lang),
                            'day': tell('mday_temp', lang),
                            'hour': tell('hour_temp', lang),
                            'minute': tell('min_temp', lang)
                }
                date_list = [deadline.get(key, template.get(key)) for key in keys]
                year, month, day, hour, min = date_list
                date = f"{day:02}.{month:02}.{year:04} {hour:02}:{min:02}"
                text = f"{tell('deadline_of_order', lang, ignore_all_insets=True)}\n<code>{date}</code>\
                \n<i>{tell('deadline_menu_desc', lang)}</i>"
                return self.send_message(ID, text, reply_markup=menu, parse_mode='HTML')
            case "edit_description_menu":
                menu.add(button(tell("enter", lang), callback_data=f"enter description {order_id}"))
                menu.add(button(tell("clear", lang), callback_data=f"del description {order_id}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                desc = order["description"]
                if not desc:
                    desc = tell("description_desc", lang)
                else:
                    desc = f'<code>{desc}</code>'+'\n<i>'+tell('description_disc', lang)+'</i>'
                text = f"{tell('description_of_order', lang, {'curr': desc})}"
                self.send_message(ID, text, reply_markup=menu, parse_mode='HTML')
            case "edit_order_menu":
                menu.add(button(tell("type_of_order", lang, {'curr': tell(f"{order['type']}", lang)}),
                                callback_data=f'to type_of_order#{order_id}'))
                curr_desc = order['description']
                if not curr_desc:
                    curr_desc = tell("None")
                menu.add(button(tell("description_of_order", lang, {'curr': curr_desc}), 
                                callback_data=f'to description_of_order#{order_id}'))
                master = order['master']
                if master:
                    menu.add(button(tell("master_of_order", lang), f"to master#{master}"))
                menu.add(button(tell("reference_of_order", lang, {'curr': str(len(order['reference'].keys()))}),
                                callback_data=f'to reference_of_order#{order_id}'))
                curr_dl = order['deadline']
                if curr_dl == '~':
                    curr_dl = tell("None")
                menu.add(button(tell("deadline_of_order", lang, {'curr': curr_dl}),
                                callback_data=f"to deadline#{order_id}"))
                prev = order['prev']
                # menu.add(button(tell("logging_of_order", lang), callback_data=f"to logging {order_id}"))
                if prev:
                    menu.add(button(tell("previous_of_order", lang), callback_data=f"to show_order#{prev}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                ready, columns = self.ready_to_distribute(order_id, lang)
                text = f"{tell('draft', lang, {'id': order_id})}\n\n{tell('draft_desc', lang)}\n\n{tell(ready, lang, {'columns': columns})}"
                self.send_message(ID, text, parse_mode="HTML", reply_markup=menu)
            case "edit_reference_menu":
                menu.add(button(tell("viewe_files", lang, inset={'curr': str(len(order['reference'].keys()))}), 
                                callback_data=f"to reference_viewer#{order_id}"))
                if order.get("status") == "created":
                    menu.add(button(tell("delete_reference", lang), callback_data=f"to reference_deleter#{order_id}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                text = f"{tell('reference_of_order', lang, ignore_all_insets=True)[:-2]}\n{tell('edit_reference_desc', lang)}"
                msg = self.send_message(ID, text, parse_mode="HTML", reply_markup=menu)
                self.set_msg_to_del(user, msg)
            case "edit_type_menu":
                pass
            case "enter_description_menu":
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                self.send_fielde(user, "description", order_id, repl=menu)
            case "good_file":
                self.send_message(ID, tell("good_file", lang, {'file_name': user.get('file_name')}))
            case "main_menu":
                if user['status'] != 'newcomer':
                    menu.add(button(tell('my_orders', lang), callback_data='to my_orders'))
                menu.add(button(tell('new_order', lang), callback_data='to new_order'))
                if user['status'] in {'god', 'master'}:
                    menu.add(button(tell('my_projects', lang), callback_data="to my_projects"))
                menu.add(button(tell('manuals', lang), callback_data='to manuals'))
                menu.add(button(tell('settings', lang), callback_data='to settings'))
                menu.add(button(tell('fitback', lang), callback_data='to fitback'))
                self.send_message(ID, tell('main_menu', lang), reply_markup=menu)
            case "my_orders_menu":
                menu.add(self.display(user, "back"))
                text = f"{tell('my_orders', lang)}\n\n{tell('my_orders_desc', lang)}"
                self.send_message(ID, text, parse_mode="HTML")
            case "settings_menu":
                menu.add(button(tell("profile", lang), callback_data="to profile"))
                menu.add(button(tell("language", lang), callback_data="to language"))
                menu.add(self.display(user, "back"))
                self.send_message(ID, tell("settings", lang), reply_markup=menu)
            case "language_menu":
                menu.add(button(tell("system_language", lang), callback_data="switch sys_lang"))
                for lng in language_codes:
                    menu.add(button(tell("language_codes", lng), callback_data=f"switch language {lng}"))
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                current = self.current_switch(user, "language_menu")
                text = f"{tell('language', lang)}\n<i>{tell('now_selected', lang)}</i>: {tell(current, lang)}"
                self.send_message(ID, text, parse_mode="HTML", reply_markup=menu)
            case "profile_menu":
                menu.add(button(tell("become_master", lang), callback_data="request master"))
                menu.add(button(tell("discard_profile", lang), callback_data="del profile"))
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                inset = {
                    'id': user['id'], 
                    'username': user['username'], 
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    # 'language_code': user['language_code'],
                    'status': user['status'],
                    'reputation': user['reputation'],
                    'filters': user['filters'].replace('/', '\n'),
                }
                text = f"{tell('profile', lang)}\n{tell('passport', lang, inset=inset)}\n{tell('profile_disc', lang)}"
                self.send_message(ID, text, reply_markup=menu, parse_mode='HTML')
            case "reference_deleter":
                reference:dict = order.get("reference")
                select_code = user.get('selected', 0)
                l = len(reference)
                selected = f"{'0'*l}{bin(select_code)[2:]}"[-l:]
                # selected = f"{int(bin(select_code)[2:]):0{l}}"
                f_id:str
                f_info:dict
                for i, item in enumerate(sorted(reference.items())):
                    f_id, f_info = item
                    f_name = f_info.get("f_name", f'file{i}')
                    select = select_code ^ 2**(l-i-1)
                    menu.add(button('❌'*(selected[i] == '1')+f_name, callback_data=f"s|rd|{select}"))
                optional_line = []
                if '0' in selected and reference:
                    optional_line.append(button(tell("select_all", lang), callback_data=f"s|rd|{int('1'*l, 2)}"))
                if select_code:
                    optional_line.append(button(tell("clear_selection", lang), callback_data="s|rd|0"))
                menu.add(*optional_line)
                if select_code:
                    menu.add(button(tell("delete_all_selected", lang), callback_data=f"del sr {select_code}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                if "msg_id" in user:
                    self.edit_message_reply_markup(ID, user.get("msg_id"), reply_markup=menu)
                else:
                    self.send_message(ID, tell("reference_deleter", lang), reply_markup=menu)
            case "reference_viewer":
                reference:dict = order.get("reference", {})
                for f_id, f_info in reference.items():
                    f_name = f_info.get('f_name')
                    menu.add(button(f_name, callback_data=f"to file#{order_id}#r#{f_id}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                self.send_message(ID, tell("reference_viewer", lang, inset={'loc': tell("reference_of_order", lang, ignore_all_insets=True)}), reply_markup=menu)
            case "view_file":
                f_id, loc = user.get('f_id'), user.get('f_loc')
                folder:dict = order.get(loc)
                file_info = self.document_upload(folder.get(f_id, {}), f_id)
                if user['status'] in {'god', 'master', 'foreman'} or order['status'] == 'created':
                    menu.add(button(tell("delete_file", lang), callback_data=f"del file {order_id} r {f_id}"))
                menu.add(self.display(user, "back"))
                self.send_document(ID, **file_info, reply_markup=menu)
            case "unknw_des":
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                self.send_message(ID, tell("unknw_des", lang), reply_markup=menu)
                if "msg_id" in user:
                    self.delete_message(ID, user.get('msg_id'))
            case "switch":
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                self.send_message(ID, tell("switch", lang), reply_markup=menu)
            case "back_to_home":
                return button("◀️🏛", callback_data="to main_menu")
            case "back":
                path: list = user['nav'].split('/')
                if len(path) == 1:
                    destination = "main_menu"
                elif len(path) > 1:
                    destination = path.pop(-2)
                if '#' in destination:
                    destination, dest_id = destination.split('#')[:2]
                    dest_id = '#' + dest_id
                else:
                    dest_id = ''
                but = button(
                    tell("back", lang, {'where': tell(destination, lang, ignore_all_insets=True)}), 
                    callback_data=f"to {destination}{dest_id}"
                )
                return but
            case _:
                self.display(user, 'unknw_des')
    
    
    @exc.protect
    def current_switch(self, user:dict, code:str) -> str:
        match code:
            case "language_menu":
                if user["sys_lang"]:
                    return "system_language"
                return "language_codes"
    

    def document_download(self, message: telebot.types.Message, folder_path) -> tuple[str, dict]:
        try:
            document:telebot.types.Document = getattr(message, "document", None)
            audio: telebot.types.Audio = getattr(message, "audio", None)
            if document is None:
                document = audio
            file_info = self.get_file(document.file_id)
            file_bytes = self.download_file(file_info.file_path)
            file_name = document.file_name
            # file_decoded = str(file_bytes, encoding='ISO-8859-1')
            path = folder_path + file_name
            file = {
                'order_id': path[:path.find('/')],
                'path': path,
                'bytes': file_bytes
            }
            ID = self.files_data.upload_file(file)
            file_info = {"f_name":file_name, "tg_id": document.file_id}
            return ID, file_info
        except Exception as e:
            self.reply_to(message, e)

    def document_upload(self, file_info:dict, f_id) -> str|bytes:
        try:
            tg_id = file_info.get('tg_id')
            file_info = self.get_file(tg_id)
            return {'document': tg_id}
        except:
            f_name = file_info.get('f_name')
            file = self.files_data.download_file(f_id)
            return {'document': file, 'visible_file_name': f_name}

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
        match loc:
            case "reference_of_order":
                add_on = self.document_download(message, f"{order_id}/reference/")
                if add_on is None:
                    return
                add_on_id, add_on_info = add_on
                documents: dict = self.orders_data.fetch(order_id).get('reference', {})
                documents.update({add_on_id: add_on_info})
                # documents = json.dumps(documents).encode('ISO-8859-1')
                documents = json.dumps(documents).encode('utf-8')
                request = {"reference": documents}
                func = self.orders_data.update_order
                display_code = "edit_reference_menu"
            case _:
                return
        func(order_id, request)
        user.update({'file_name': add_on_info.get("f_name", 'unnknow file_name')})
        self.display(user, 'good_file') 
        try:
            self.delete_message(chat_id, msg_id)
            self.display(user, display_code)
        except:
            pass


    def text_handler(self, message:telebot.types.Message, user: dict, path_end: str) -> None:
        if path_end == 'del_profile' and message.text == str(user['id']):
            logger.info(f"{self.users_data.discard_profile(user['id'])}")
            del user
            del message
            return
        id_list = list(map(try_int, re.findall(r'(?<=#)\d*', path_end)))
        location = (re.findall(r'.*(?=#)')+[None])[0]
        if location is None:
            return
        match location:
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
                request = {"deadline": dl}
                self.orders_data.update_order(order_id, request)
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
                        request = {'description': message.text}
                        func = self.orders_data.update_order
        func(ID, request)
        self.delete_message(chat_id, message_id)
        self.display(user, 'switch')
    

    @exc.protect
    def ban(self, ID, date:str='~', ban_reason='other'):
        user = self.users_data.fetch(ID)
        lang = user.get('lang')
        request = {"status": "banned", "_unban_date": date}
        self.users_data.update_profile(ID, request)
        # if 
        self.send_message(ID, tell("ban_notification", inset={'reason': tell(ban_reason, lang), 'date': date}))

    @exc.protect
    def spam(self, text, parse_mode):
        logger.info(f"spam {f'{text=}':20s}, {parse_mode=}"[:100])
        for ID in self.users_data.search():
            user = self.users_data.fetch(ID)
            if user.get('status') != 'god':
                continue
            logger.info(f"\t{ID}")
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
        if user['sys_lang']:
            lang = message.from_user.language_code
            if lang != user['language_code']:
                self.users_data.update_profile(ID, request={'language_code': lang})
                user['language_code'] = lang
        return user    


    @exc.protect
    def new_order(self, user:dict) -> int:
        ID = user['id']
        order_id = self.orders_data.new_order(user)
        match user['status']:
            case 'banned':
                self.display(user, "banned")
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
