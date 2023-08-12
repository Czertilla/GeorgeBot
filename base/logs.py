from .base import *

class Logs(MetaBase.BasicBase, metaclass=MetaBase):
    def new_log(self, anchor, log, date)->None:
        ID = self.gen_id()
        request = {'id': ID,
                    'time': date,
                    'log': log,
                    'anchor': anchor}
        self.insert(request)