from .Gbot import GeorgeBot, clock

class CalendaryMixin:
    def available_hours(self:GeorgeBot, user:dict) -> list:
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
    
    def available_minutes(self:GeorgeBot, user:dict) -> list:
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
