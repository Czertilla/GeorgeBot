from .Gbot import *

class DisplayMixin:
    @exc.protect
    def display(self:GeorgeBot, user:dict, code:str) -> None|telebot.types.InlineKeyboardButton|telebot.types.Message:
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
            order:dict = self.orders_data.fetch(order_id)
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
