from .base import *

class Events(MetaBase.BasicBase, metaclass=MetaBase):       
    def new_event(self, event:dict):
        ID = self.gen_id()
        regularity = self.convert(event.get('regularity'))
        exceptions = self.convert(event.get('exceptions'))
        event.update({"id": ID,"regularity":regularity,'exceptions':exceptions})
        self.insert(event)
        return ID 
    
    def convert(self, obj):
        match type(obj).__name__:
            case 'dict':
                regularity = clock.timedelta(**obj).total_seconds()
                return clock.try_int(regularity)
            case 'int':
                return (regularity:=obj)
            case 'list':
                exceptions = '/'.join(obj)
                return exceptions
            case 'str':
                return (exceptions:=obj)
            case _:
                return obj
    
    def fetch(self, ID):
        result = super().fetch(ID)
        for key, val in result.copy().items():
            if val is None:
                result.pop(key)
        exceptions:str = result.get('exceptions', '')
        result.update({"exceptions": exceptions.split('/')})
        return result
    
    def update_event(self, ID, request:dict, /, autoencode:bool=True):
        for key, val in request.items():
            match key:
                case 'event':
                    ID = self.new_event(val)
                    return ID
                case 'regularity'|'exceptions':
                    self._update(ID, key, self.convert(val))
                case _:
                    if key not in self.columns:
                        continue
                    self._update(ID, key, val)
        return ID
