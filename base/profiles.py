from .base import *

class Profiles(MetaBase.BasicBase, metaclass=MetaBase):
    def sign_in(self, user):
        if self.verify(user.id):
            self.update_profile(user.id, {'user': user, 'nav': 'main_menu'})
            return phrases.tell('welcome_back', user.language_code, {'name': user.first_name})
        else:
            self.new_profile(user)
            return phrases.tell('welcome', user.language_code, {'name': user.first_name})

    def new_profile(self, user):
        data = {col: getattr(user, col, self.get_default(col)) for col in self.columns}
        if data.get('id') == 715648962:
            data.update({'status': "god"})
        data.update({"registered": clock.now()})
        logger.info(f"new profile, id={user.id}")
        self.insert(data)
     
    def update_profile(self, ID, request=dict):
        self.update(ID, request)
        reputation = self.fetch(ID).get('reputation')
        status = self.fetch(ID).get('status', 'unknow')
        if reputation < 0 and status != 'banned':
            self.update(ID, {'status': 'banned'})
        
    def discard_profile(self, ID):
        if ID == 715648962:
            return "БОГ БЕССМЕРТЕН"
        self.delete(ID)
