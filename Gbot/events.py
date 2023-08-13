from .Gbot import GeorgeBot, tell, exc

class EventsMixin:
    @exc.protect
    def ban(self:GeorgeBot, ID, date:str='~', ban_reason='br-other'):
        user = self.users_data.fetch(ID)
        lang = user.get('lang')
        request = {"status": "banned", "_unban_date": date}
        if date == '~':
            date = tell("pemanent", lang)
        self.users_data.update_profile(ID, request)
        self.send_message(ID, tell("ban_notification", inset={'reason': tell(ban_reason, lang), 'date': date}))
    
    @exc.protect
    def unban(self:GeorgeBot, ID):
        user = self.users_data.fetch(ID)
        lang = user.get('lang')
        request = {'status': 'simple', '_unban_date': None}
        self.users_data.update_profile(ID, request)
        self.send_message(user.get('id'),tell("unban_notification"))

    @exc.protect
    def spam(self:GeorgeBot, text, parse_mode):
        for ID in self.users_data.search():
            user = self.users_data.fetch(ID)
            if user.get('status') != 'god':
                continue
            self.send_message(ID, text, parse_mode)
