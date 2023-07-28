import datetime
import logging
import splitter
import time
from try_int import try_int
from last_mday import get_last_mday

logger = logging.getLogger(__name__)

def timedelta(*args, **kwargs):
    keys = ('days', 'seconds', 'microseconds','milliseconds', 'minutes', 'hours', 'weeks')
    return datetime.timedelta(*args, **{key: kwargs.get(key, 0) for key in keys})

def now(*modifiers:str, dict_like:bool=False):
    moment = datetime.datetime.now()
    for modifier in modifiers:
        moment = _modify(moment, modifier)
    if dict_like:
        return package(moment)
    return f"{moment.year:04}-{moment.month:02}-{moment.day:02} {moment.hour:02}:{moment.minute:02}:{moment.second:02}"

def _modify(moment:datetime.datetime, modifier:str) -> datetime.datetime:
    modifier = modifier.replace(' ', '')
    if moment is None:
        return _get_modifier(modifier[1:], sensitivity=True)
    match modifier[0]:
        case '+':
            return moment + _get_modifier(modifier[1:])
        case '-':
            return moment - _get_modifier(modifier[1:])
        case _:
            return moment
    
def _get_modifier(modifier:str, sensitivity=False) -> datetime.timedelta:
    num = ''
    while modifier[0].isdigit():
        num += modifier[0]
        modifier = modifier[1:]
    num = try_int(num)
    if num is None:
        return datetime.timedelta()
    match modifier:
        case 'day' | 'days' | 'D' | 'd':
            return datetime.timedelta(days=num)
        case 'hour' | 'hours' | 'H' | 'h':
            return datetime.timedelta(hours=num)
        case 'min' | 'mins' | 'minute' | 'minutes' | 'M', 'm':
            return datetime.timedelta(minutes=num)
        case 'sec' | 'secs'| 'second' | 'seconds' | 'S' | 's':
            return datetime.timedelta(seconds=num)
        case 'week' | 'weeks' | 'w' | 'W': 
            return datetime.timedelta(weeks=num)
    if sensitivity:
        return 
    return datetime.timedelta()


def get_datetime(line)-> datetime.datetime|None:
    try:
        return datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")
    except:
        logger.warning(f"invalid date_string_format: {line} -> %Y-%m-%d %H:%M:%S")
        return None
    
def get_dateline(date:datetime.datetime) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")


def package(moment:str|datetime.datetime, gradation:str='', ignore_nulls:bool=False) -> dict:
    dictionary = {}
    match gradation:
        case '' | 'standart':
            keys = ('year', 'month', 'day', 'hour', 'minute', 'second')
            pattern = "%Y-%m-%d %H:%M:%S"
            sep = '-'
        case 'normal':
            keys = ('day', 'month', 'year', 'hour', 'minute', 'second')
            pattern = "%d.%m.%Y %H:%M:%S"
            sep = '.'
        case 'date':
            keys = ('year', 'month', 'day')
            pattern = '%Y-%m-%d'
            sep = '-'
        case 'ndate':
            keys = ('day', 'month', 'year')
            pattern = "%d.%m.%Y"
            sep = '.'
        case 'time':
            keys = ('hour', 'minute', 'second')
            pattern = "%H:%M:%S"
            sep = '-'
        case "ntime":
            keys = ('hour', 'minute')
            pattern = "%H:%M"
            sep = '.'
    match type(moment):
        case datetime.datetime:
            for key in keys: 
                val = getattr(moment, key)
                if val is None and ignore_nulls:
                    continue
                dictionary.update({key: val})
        case str:
            try:
                D = datetime.datetime.strptime(moment, pattern)
                dictionary = package(D, gradation, ignore_nulls)
                D = package(D, gradation, ignore_nulls)
            except:
                date, time_nums = (splitter.split(moment) + [None]*2)[:2]
                vals = (list(map(try_int, (splitter.split(date, sep)))) + [None]*3)[:3] + (list(map(try_int, splitter.split(time_nums, ':'))) + [None]*3)[:3]
                if vals[2] is None:
                    if vals[1] is not None:
                        if vals[1] > 12:
                            vals.pop(2)
                            vals = [None] + vals
                for i, key in enumerate(keys):
                    val = vals[i]
                    if val is None and ignore_nulls:
                        continue
                    dictionary.update({key: vals[i]})
            # if D != dictionary:
            #     print('AAAAAAAAAAAAAAAAAAAAAAAA\n',D,'\n',dictionary,'\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    return dictionary


def wait(s=0.1):
    time.sleep(s)


# print(now())
