import logging
import telebot
from base import getBase, Profiles, Orders, Files 
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
    def display(self, user: dict, code: str) -> None|telebot.types.InlineKeyboardButton|telebot.types.Message:
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
            case "ban_menu"|"report_menu":
                m = code.split('_')[0]
                target = user.get('ban_target')
                menu.add(button(tell("br-abusive_behavior", lang), callback_data=f'{m}#{target}#abusive_behavior'))
                menu.add(button(tell("br-bug_exploits", lang), callback_data=f'{m}#{target}#bug_exploits'))
                menu.add(button(tell('br-financial_fraud', lang), callback_data=f'{m}#{target}#financial_fraud'))
                menu.add(button(tell('br-other', lang), callback_data=f"{m}#{target}#other"))
                menu.add(self.display(user, "back"))
                self.send_message(ID, text="set_ban_reason", reply_markup=menu)
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
                date = f'{year}-99-99 99:99'
                menu.add(button(tell("select_datetime", lang, inset={'date': date}), callback_data=f"deadline#{order_id}#{date}:99"))
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
                        row.append(button(day, callback_data=f"calendary#{year}-{month}-{dig_day}#{note}"))
                        # row.append(button(day, callback_data=f"calendary#{year}-{month}-{day}"))
                    else:
                        row.append(button(text='<', callback_data=topbar[0].callback_data))
                    weekday += 1
                if 0 < weekday < 7:
                    row += [button(text='>', callback_data=topbar[-1].callback_data)]*(7-weekday) 
                menu.add(*row)
                date = f'{year:02}-{month:02}-99 99:99'
                menu.add(button(tell("select_datetime", lang, inset={'date': date}), 
                                callback_data=f"deadline#{order_id}#{date}:99"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "calendary_hours":
                timeline = user.get('timeline')
                def set_hour(h):
                    if h in timeline:
                        return button(f"{h:02}: - -", callback_data=f"calendary#{year}-{month}-{day} {h}#{note}")
                    return button(f"XX:XX", callback_data=f"X")
                menu = telebot.types.InlineKeyboardMarkup(row_width=6)
                year, month, day = user.get("year"), user.get('month'), user.get('day')
                menu.add(button(f"{year}", callback_data=f"calendary##{note}"),
                         button(f"{tell(self.months[month], lang)}", callback_data=f"calendary#{year}#{note}"),
                         button(f"{day}", callback_data=f"calendary#{year}-{month}#{note}"))
                for line in range(4):
                    menu.add(*
                        [set_hour(hour) for hour in range(line*6, line*6+6)])
                date = f'{year}-{month:02}-{day:02} 99:99'
                menu.add(button(tell("select_datetime", lang, inset={'date': date}), callback_data=f"deadline#{order_id}#{date}:99"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:    
                    exc.tracebacking()
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "calendary_minutes":
                timeline = user.get('timeline')
                def set_minute(m):
                    if m in timeline:
                        return button(f"{hour:02}:{m:02}", callback_data=f"calendary#{year}-{month}-{day} {hour}:{m}#{note}")
                    return button(f"XX:XX", callback_data=f"X")
                menu = telebot.types.InlineKeyboardMarkup(row_width=6)
                year, month, day, hour = [user.get(key) for key in ('year', 'month', 'day', 'hour')]
                menu.add(button(f"{year}", callback_data=f"calendary##{note}"),
                         button(f"{tell(self.months[month], lang)}", callback_data=f"calendary#{year}#{note}"),
                         button(f"{day}", callback_data=f"calendary#{year}-{month}#{note}"),
                         button(f"{hour}: - -", callback_data=f"calendary#{year}-{month}-{day}#{note}"))
                for line in range(10):
                    menu.add(*
                        [set_minute(minute) for minute in range(line*6, line*6+6)])
                date = f'{year}-{month:02}-{day:02} {hour:02}:99'
                menu.add(button(tell("select_datetime", lang, inset={'date': date}), callback_data=f"deadline#{order_id}#{date}:99"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:    
                    exc.tracebacking()
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "calendary_finaly":
                menu = telebot.types.InlineKeyboardMarkup(row_width=5)
                year, month, day, hour, minute = [user.get(key) for key in ('year', 'month', 'day', 'hour', 'minute')]

                date_time = clock.get_datetime(f"{year}-{month:02}-{day:02} {hour:02}:{minute:02}:00")
                upMonth = f"calendary#{year}-{month+1}-{day} {hour}:{minute}#{note}"
                dwMonth = f"calendary#{year}-{month-1}-{day} {hour}:{minute}#{note}"
                match month:
                    case 12:
                        upMonth = f"calendary#{year+1}-{1}-{day} {hour}:{minute}#{note}"
                    case 1:
                        dwMonth = f"calendary#{year-1}-{12}-{day} {hour}:{minute}#{note}"
                upDay = f"calendary#{clock.get_dateline(date_time+clock.datetime.timedelta(days=1))[:-3]}#{note}"
                dwDay = f"calendary#{clock.get_dateline(date_time-clock.datetime.timedelta(days=1))[:-3]}#{note}"
                upHour = f"calendary#{clock.get_dateline(date_time+clock.datetime.timedelta(hours=1))[:-3]}#{note}"
                dwHour = f"calendary#{clock.get_dateline(date_time-clock.datetime.timedelta(hours=1))[:-3]}#{note}"
                upMin = f"calendary#{clock.get_dateline(date_time+clock.datetime.timedelta(minutes=1))[:-3]}#{note}"
                dwMin = f"calendary#{clock.get_dateline(date_time-clock.datetime.timedelta(minutes=1))[:-3]}#{note}"
                menu.add(button(f"🔼", callback_data=f"calendary#{year+1}-{month}-{day} {hour}:{minute}#{note}"),
                         button(f"🔼", callback_data=upMonth),
                         button(f"🔼", callback_data=upDay),
                         button(f"🔼", callback_data=upHour),
                         button(f"🔼", callback_data=upMin)
                         )
                menu.add(button(f"{year}", callback_data=f"calendary##{note}"),
                         button(f"{tell(self.months[month], lang)}", callback_data=f"calendary#{year}#{note}"),
                         button(f"{day:02}", callback_data=f"calendary#{year}-{month}#{note}"),
                         button(f"{hour:02}", callback_data=f"calendary#{year}-{month}-{day}#{note}"),
                         button(f":{minute:02}", callback_data=f"calendary#{year}-{month}-{day} {hour}#{note}")
                         )
                menu.add(button(f"🔽", callback_data=f"calendary#{year-1}-{month}-{day} {hour}:{minute}#{note}"),
                         button(f"🔽", callback_data=dwMonth),
                         button(f"🔽", callback_data=dwDay),
                         button(f"🔽", callback_data=dwHour),
                         button(f"🔽", callback_data=dwMin)
                         )
                date = f'{year}-{month:02}-{day:02} {hour:02}:{minute:02}'
                menu.add(button(tell("select_datetime", lang, inset={'date': date}), callback_data=f"deadline#{order_id}#{date}:99"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                try:
                    msg_id = user.get("msg_id", 0)
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                except:     
                    exc.tracebacking()
                    self.send_message(ID, f"{year}", reply_markup=menu)
            case "confirm_del_files":
                menu.add(button(tell("cancel_deletion", lang), callback_data="confirm cancel"))
                menu.add(button(tell("confirm_deletion", lang), callback_data="confirm del"))
                self.send_message(ID, tell("confirm_deletion_files", lang), reply_markup=menu)
            case "confirm_del_profile":
                menu.add(self.display(user, 'back'))
                menu.add(self.display(user, 'back_to_home'))
                self.send_message(ID, tell("del_profile_warning", lang, {'id': user['id']}), reply_markup=menu, parse_mode="HTML")
            case "confirm_del_order":
                
                pass
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
                desc = order["description"][:3500]
                if not desc:
                    desc = tell("description_desc", lang)
                else:
                    desc = f"<code>{desc}</code>\n<i>({len(desc)}/3500)\n{tell('description_disc', lang)}</i>"
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
                if order.get('satus') in ('created', 'recreated'):
                    menu.add(button(tell('delete_order_draft', lang), callback_data=f"del order {order_id}"))
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
                if order.get('status') not in {"created", "recreated"}:
                    self.display(user, "show_order")
                    return
                for ser, data in self.get_services().items():
                    menu.add(button(tell("service_face", 
                                         lang, 
                                         inset={
                                             "serv": ser,
                                             "price": data.get('min_price')
                                         }), 
                                    callback_data=f"switch type {ser}#{order_id}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                self.send_message(ID, 
                                  tell("type_of_order", lang, inset={'curr': tell(f'{order.get("type")}', lang)}), 
                                  reply_markup=menu)
            case "enter_description_menu":
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                self.send_fielde(user, "description", order_id, repl=menu)
            case "good_file":
                self.edit_message_text(tell("good_file", lang, {'file_name': user.get('file_name')}),
                                       user.get('load_cht_id'),
                                       user.get('load_msg_id')
                                       )
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
            case "my_orders_menu"|"my_projects_menu":
                match code:
                    case "my_orders_menu":
                        kwargs = {'customer': user}
                        lc = 'o'
                    case "my_projects_menu":
                        kwargs = {'master': user}
                        lc = 'p'
                o_dict = self.get_orders(**kwargs)
                stat_list = ['accepted', 'proposed', 'distributed', 'drafts', 'archive']
                opened_code = user.get('selected', 0)
                l = len(stat_list)
                opened= f"{'0'*l}{bin(opened_code)[2:]}"[-l:]
                for i, stat in enumerate(stat_list):
                    id_list = o_dict.get(stat)
                    if not id_list:
                        continue
                    t = {'0':'▶️', '1':'🔽'}.get(opened[i])
                    select = opened_code ^ 2**(l-i-1)
                    menu.add(button(f"{t}{stat.upper()}", callback_data=f"s|m{lc}|{select}"))
                    if t=='🔽':
                        for o_id in id_list:
                            menu.add(button(o_id, callback_data=f'to edit_order#{o_id}'))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                text = f"{tell('my_orders', lang)}\n\n{tell('my_orders_desc', lang)}"
                if msg_id:=user.get('msg_id'):
                    self.edit_message_reply_markup(ID, msg_id, reply_markup=menu)
                else:
                    self.send_message(ID, text, reply_markup=menu, parse_mode="HTML")
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
                    f_name = f_info.get("name", f'file{i}')
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
                    f_name = f_info.get('name', 'unknow file')
                    menu.add(button(f_name, callback_data=f"to file#{order_id}#r#{f_id}"))
                menu.add(*[self.display(user, "back"), self.display(user, "back_to_home")])
                self.send_message(ID, 
                                  tell("reference_viewer", 
                                       lang, 
                                       inset={'loc': tell("reference_of_order", 
                                                          lang, 
                                                          ignore_all_insets=True)}), 
                                  reply_markup=menu)
            case "too_many_orders":
                menu.add(self.display(user, "back"))
                menu.add(self.display(user, "back_to_home"))
                self.send_message(ID, text = tell("too_many_orders", lang), reply_markup=menu)
                pass
            case "view_file":
                f_id, loc = user.get('f_id'), user.get('f_loc')
                folder:dict = order.get(loc)
                file_info = self.document_upload(folder.get(f_id, {}), f_id)
                if user['status'] in {'god', 'master', 'foreman'} or order['status'] == 'created':
                    menu.add(button(tell("delete_file", lang), callback_data=f"del file {order_id} r {f_id}"))
                menu.add(self.display(user, "back"))
                self.send_document(ID, **file_info, reply_markup=menu, protect_content=True)
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
            case "invalid_date":
                return tell('invalid_date', lang)
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