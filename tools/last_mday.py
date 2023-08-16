# import logging


def get_last_mday(month:int, year:int=2001) -> int:
    match month:
        case 1 | 3 | 5 | 7 | 8 | 10 | 12:
            last_day = 31
        case 2:
            last_day = int(year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) + 28
        case _:
            last_day = 30
    return last_day

# logger = logging.getLogger(__name__)