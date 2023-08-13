import logging
from typing import overload
import telebot
from base import getBase, Profiles, Orders, Files 
from exceptor import Exceptor
from phrases import tell
from phrases import language_codes
from try_int import try_int
import clock
import json
import re

logger = logging.getLogger(__package__)
exc = Exceptor()
class GeorgeBot:...

from .buffer import Buffer
from .unknw import uknw

from .access import AccessMixin
from .calendary import CalendaryMixin
from .display import DisplayMixin
from .events import EventsMixin
from .files import FilesMixin
from .handlers import HandlersMixin
from .users import UsersMixin
from .orders import OrdersMixin 

class GeorgeBot(
    telebot.TeleBot,
    AccessMixin,
    CalendaryMixin,
    DisplayMixin,
    EventsMixin,
    FilesMixin,
    HandlersMixin,
    UsersMixin,
    OrdersMixin
    ):
    def __init__(self, token, u_d:Profiles, o_d:Orders):
        telebot.TeleBot.__init__(self, token, num_threads=50)
        files_data:Files = getBase("Files")
        self.download_buffer = Buffer()
        self.files_data = files_data
        self.users_data = u_d
        self.orders_data = o_d
        self.months = ['month', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        self.weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
    
    @exc.protect
    def current_switch(self, user:dict, code:str) -> str:
        match code:
            case "language_menu":
                if user["sys_lang"]:
                    return "system_language"
                return "language_codes"
    
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

    def get_command(self, message: telebot.types.Message):
        match type(message):
            case type(''):
                text = message
            case telebot.types.Message:
                text = message.text
        sintax = text.split()
        com, args = sintax[0], sintax[1:]

if __name__ == "__main__":
    GeorgeBot("1", Profiles(), Orders())