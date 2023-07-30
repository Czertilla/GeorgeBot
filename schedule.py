from base import Events
import threading
import datetime
import clock
import logging
from Gbot import GeorgeBot
import json
import exceptor

logger = logging.getLogger(__name__)
exc = exceptor.Exceptor()

class Scheduler:
    def __init__(self, bot:GeorgeBot) -> None:
        self.lock = False
        self.closing = False
        self.timetable:Events = Events()
        self.timers = {}
        self.bot = bot
    
    @exc.protect
    def schedule(self):
        if self.closing:
            return
        while self.lock:
            if self.closing:
                return
        self.lock = True
        for key in self.timers.copy():
            val = self.timers.get(key)
            val.cancel()
            val.join()
        self.lock = False
        self.timers = {}
        for ID in self.timetable.search(1, ('active',)).get('whole').get(''):
            self.add_timer(ID)
    
    @exc.protect
    def add_event(self, code, event_data:dict):
        scion = event_data.get('scion')
        event_id = event_data.get('event_id')
        code = event_data.get('code').split('.')
        args = []
        kwargs = {}
        match code[0]:
            case "test":
                regularity = event_data.get('regularity')
                exceptions = event_data.get('exceptions')
                func = self.bot.spam
                text = f"""Это тестовая рассылка по расписанию
<code>проверка парсинга, этот текст должен копироваться по нажатию</code>
<i>ID события: ({code[-1]}){event_id}
Частота рассылки:{regularity}
За исключением {exceptions}
следующая дата рассылки {scion}</i>"""
                args += [text]
                kwargs.update({"parse_mode": "HTML"})
            case "advertisement":
                func = self.bot.advert()
            case "unban":
                func = self.bot.unban
                args += [code[1]]
            case "wait4":
                target = code[1]
                func = self.set_event_data
                args += [target, 'on']
            case _:
                return {}
        return {"function": self.get_func(func, event_id, scion), "args": args, "kwargs": kwargs}
    
    
    @exc.protect
    def add_timer(self, event_id, ignore_past=False):
        if self.closing:
            return
        while self.lock:
            if self.closing:
                return
        event_data:dict = self.timetable.fetch(event_id)
        time = event_data.get('time')
        done = event_data.get('done', 0)
        active = event_data.get('active', 1)
        if time == '~' or done or not active:
            if done and not event_data.get('regularity', False):
                self.timetable.update_event(event_id, {"active": 0})
            return
        regularity = event_data.get('regularity')
        exceptions = event_data.get('exceptions')
        if regularity:
            delta = datetime.timedelta(seconds=regularity)
            scion = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + delta
            checklist = [lambda scion: scion.strftime("%Y-%m-%d %H:%M:%S") < clock.now()]
            for exception in exceptions:
                match exception:
                    case 'night':
                        check = lambda scion: scion.hour < 5
                    case 'weekend':
                        check = lambda scion: scion.weekday() >= 5
                    case None:
                        check = lambda scion: False
                    case _:
                        date = clock.package(exception, ignore_nulls=True)
                        check = lambda scion: all(getattr(scion, key) == date.get(key) for key in date.keys())
                checklist.append(check)
            while any(check(scion) for check in checklist):
                scion += delta
            scion = scion.strftime("%Y-%m-%d %H:%M:%S")
        else:
            scion = None
        event_data.update({"event_id": event_id, 'scion': scion})
        data = self.add_event(event_data.get('code'), event_data)
        delta = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") - datetime.datetime.now()
        seconds = max(delta.total_seconds(), 0)
        if seconds > 604800:
            self.set_event_data(event_id, 'off')
            self.new_event({"code":f"wait4.{event_id}", 'time': clock.now("+5days")})
            return
        # if seconds > 120:
        #     self.set_event_data(event_id, 'off')
        #     self.new_event({"code":f"wait4.{event_id}", 'time': clock.now("+30seconds")})
        #     return
        elif seconds == 0 and ignore_past:
            self.set_event_data(event_id, "complete")
        timer = threading.Timer(seconds, **data)
        timer.name = event_id
        timer.daemon = bool(event_data.get('daemon', 0))
        self.timers.update({event_id: timer})
        timer.start()

    @exc.protect
    def get_func(self, func, event_id, scion=None):
        def decorated(*args, **kwargs):
            event = self.timetable.fetch(event_id)
            if event.get('active') and not event.get('done'):
                func(*args, **kwargs)
                logger.debug(f"event {event_id} completed")
            self.set_event_data(event_id, "complete")
            timer:threading.Timer = self.timers.pop(event_id)
            if scion:
                self.set_event_data(event_id, {"time": scion, 'done': 0})
        return decorated

    def new_event(self, event_data:dict):
        return self.set_event_data(None, {'event':event_data})
    
    def set_event_data(self, event_id=None, request:dict|str=''):
        timer:threading.Timer = self.timers.get(event_id)
        if not timer is None:
            timer.cancel()
        match request:
            case 'del':
                self.timetable.delete(event_id)
                return
            case 'complete':
                self.timetable.update_event(event_id, {'done': 1})
                return
            case 'off':
                self.timetable.update_event(event_id, {'active': 0})
                return
            case "resume":
                self.timetable.update_event(event_id, {'active': 1, 'done': 0})
                self.add_timer(event_id, ignore_past=True)
                return
            case "on":
                self.timetable.update_event(event_id, {'active': 1})
            case _:
                event_id = self.timetable.update_event(event_id, request)
        self.add_timer(event_id)
        return event_id

    def close(self):
        self.lock = True
        self.closing = True
        clock.wait()
        for key in self.timers.copy():
            timer:threading.Timer = self.timers.get(key)
            try:
                timer.cancel()
                timer.join()
                logger.debug(f"|\t|\t{key} timer closed")
            except:
                logger.error(f"|\t|\t{key} timer wasn`t close")
        
        

if __name__ == "__main__":
    with open("bot_presets.json", 'rb') as f:
        token = json.load(f).get('token')
    from base import Profiles, Orders
    bot = GeorgeBot(token, Profiles(), Orders())
    timetable = Scheduler(bot)
    timetable.schedule()
    event = {'code': "test", 'time': "2023-07-24 20:15:23"}
    timetable.new_event(event)
