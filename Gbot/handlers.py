from .Gbot import GeorgeBot, telebot, tell, logger, try_int, re, clock, exc

class HandlersMixin:
    def document_handler(self:GeorgeBot, message:telebot.types.Message, user:dict, path_end:str) -> None:
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


    def text_handler(self:GeorgeBot, message:telebot.types.Message, user: dict, path_end: str):
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
