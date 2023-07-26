import logging
import clock
from last_mday import get_last_mday
import datetime


logger = logging.getLogger(__name__)
def available_days(user:dict, note:str='') -> list:
    year, month = user.get('year', None), user.get('month', None)
    if year is None or month is None:
        return tuple()
    answer = []
    last_day = get_last_mday(month, year) 
    # fwd = get_weekday(year, month, 1)
    fwd = datetime.datetime.strptime(f"{year}-{month}-1", '%Y-%m-%d').weekday()
    match note:
        case "deadline":
            now:dict = clock.now(dict_like=True)
            tm_year = now.get('year')
            tm_mon = now.get('month')
            tm_mday = now.get('day')
            if year < tm_year or year == tm_year and month < tm_mon:
                answer = [(0, (fwd+(day-1))%7) for day in range(1, last_day+1)]
            elif year == tm_year and month == tm_mon:
                answer = [(0, (fwd+(day-1))%7) for day in range(1, tm_mday)] + [(day, (fwd+(day-1))%7) for day in range(tm_mday, last_day+1)]
            else:
                answer = [(day, (fwd+(day-1))%7) for day in range(1, last_day+1)]
        case _:
            answer = [(day, (fwd+(day-1))%7) for day in range(1, last_day+1)]
    return answer

def get_weekday(year, month, day)-> int:
    century_code = (0, 6, 4, 2)[(year // 100 - 19) % 4]
    if month <= 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        day -= 1
    match month:
        case 1 | 10:
            month_code = 1
        case 5:
            month_code = 2
        case 8:
            month_code = 3
        case 2 | 3 | 11:
            month_code = 4
        case 6:
            month_code = 5
        case 12 | 9:
            month_code = 6
        case 4 | 7:
            month_code = 0
    last = year % 100
    year_code = (century_code + last + last // 4) % 7
    day_code = (day + month_code + year_code) % 7
    week_day = (day_code + 5) % 7
    return week_day

if __name__ == "__main__":
    print(available_days({'year': 2000, 'month': 1}))