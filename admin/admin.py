from Gbot import GeorgeBot, exc
from base import Profiles, Orders, getBase
from constants import *
import threading
import tools.clock as clock
from schedule import Scheduler
from exceptor import Exceptor
from tools.available_days import available_days
import json
import logging

logger = logging.getLogger(__package__)

exc = Exceptor()
class Admin:...

from .polling import PollingMixin

class Admin(PollingMixin):
    def __init__(self) -> None:
        self.closed = False
        self.s = self.start
        self.c = self.close
        self._get_bot_presets()
        self.complete = False
        self.auto_restart = False
        self.a_r_deep_limit = -1
        self.a_r_deep_count = 0
        self.exceptor = Exceptor()
        self.users_data:Profiles = getBase("Profiles")
        self.orders_data:Orders = getBase("Orders")
        self.bot = GeorgeBot(getattr(self, "token", ''), self.users_data, self.orders_data)
        self.scheduler = Scheduler(self.bot)
        self.thr_presets = {
            'm': {'target': self._main, 'args': (self.bot, self.users_data, self.orders_data)},
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
                self.complete = False
        if self.complete and not self.threads:
            self.closed = True
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
        try:
            args = json.loads(' '.join(args))
        except:
            pass
        while type(args) != dict:
            try:
                args = json.loads(input("Please insert json-dict: "))
            except:
                pass
        presets = self.presets(None)
        presets.update(args)
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
    def show_data(self, name, mode="dict", *args):
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
        if self.complete or self.closed:
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
    
    @exc.protect
    def help(self, *args, **kwargs) -> None:
        logger.info(
"""
start- - - - - - to start session
close- - - - - - to close session
show_data [table_name] [mode=(dict/table/file)] - to show all data from db
set_event [mode =(new/edit/on/off/complete/resume/del)] [args =([json-like dict - for 'new'/'edit']/[id for other])]
presets- - - - - show bot_presets.json
clear_presets- - clear bot_presets.json
update_presets - update (create if not exist) bot_presets.json

""")
        
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
        self.scheduler.new_event({"code":f"unban.{ID}", "time":term})
        self.bot.ban(ID, term, reason)

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
                presets = {}
        for key, val in presets.items():
            setattr(self, key, val)
    
    def _set_presets(self, presets:dict[str]):
        with open('bot_presets.json', 'w') as f:
            try:
                json.dump(presets, f)
            except Exception as e:
                logger.warning(e)
                return
        logger.info("bot presets has been edited. to make the changes take effect, make a restart program")
    

    def __schedule(self):
        scheduler = getattr(self, 'scheduler', Scheduler(self.bot))
        scheduler.schedule()
