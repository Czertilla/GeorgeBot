import logging
import re
import sqlite3
import os
import json
import pickle
import clock
import phrases
import random
import uuid
import bz2
from exceptor import Exceptor

logger = logging.getLogger(__name__)
exc = Exceptor()

class DataDict(dict):
    def __init__(self,name,columns, *args, **kwargs):
        self.name = name
        self.date = clock.now()
        self.columns = columns
        self.set_width()
        dict.__init__(self, *args, **kwargs)
    def set_width(self):
        self.row_width = max(len(max(self.columns, key=lambda x: len(x))) + 2, 77/len(self.columns))
    def __add__(self, other):
        dict.update(self, other)
        return self
    def add(self, D:dict):
        self.update(D)
    def update(self, D:dict):
        dict.update(self, {D.pop('id'): D})
    def __str__(self):
        result = f"@{self.name:20s} %{self.date}\n"
        for key in self.columns:
            result += f"{key:{self.row_width}}"
        result += f'\n{"="*self.row_width*len(self.columns)}\n'
        for key, record in self.items():
            result += f"{str(key):{self.row_width}.{self.row_width}}"
            for col in self.columns[1:]:
                result += f"{str(record.get(col)):{self.row_width}.{self.row_width}}"
            result += f'\n{"_"*self.row_width*len(self.columns)}\n'
        return result

class MetaBase(type):
    _instance_dict = {}
    _base_path = "db/"
    _base_name = "data"
    _base_extension = "db"
    def __new__(cls, name, bases, attrs:dict={}):
        table_info = cls.get_table_info(name)
        if table_info is None:
            return
        namespace = {"_table_struct": table_info,
                     "_base_path": cls._base_path,
                     "_base_name": cls._base_name,
                     "_base_extension": cls._base_extension,
                     }
        namespace.update(**attrs)
        return super(MetaBase, cls).__new__(cls, name, bases, namespace)

    # def __init__(cls, name, bases, namespace):
    #     super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        if cls.__name__ not in cls._instance_dict:
            instance = super(MetaBase, cls).__call__(*args, **kwargs)
            cls._instance_dict.update({cls.__name__: instance})
        else:
            instance = cls._instance_dict.get(cls.__name__)
        return instance

    @classmethod
    def get_table_info(meta, name:str):
        name = name.lower()
        def get_type(sql_type):
            match sql_type:
                case "TEXT":
                    return str
                case "INTEGER"|"NUMERIC":
                    return int
                case "BLOB":
                    return bytes
                case "REAL":
                    return float
                case _:
                    return object
        _tnames = getattr(MetaBase, '_tnames', meta.get_base_names())
        if name not in _tnames:
            return
        info = meta.BasicBase.execute(meta, f"PRAGMA table_info({name})", ()).fetchall()
        table_info = {col[1]: {
                "num": col[0],
                "type": get_type(col[2]),
                "not_NULL": bool(col[3]),
                "default": col[4],
                "iskey": bool(col[5])
            } for col in info}
        return table_info

    @classmethod
    def get_base_names(meta): 
        names = meta.BasicBase.execute(meta, "SELECT name FROM sqlite_master WHERE type='table'", ()).fetchall()
        meta._tnames = [x[0] for x in names]
        return meta._tnames

    class BasicBase:
        def __init__(self): 
            # self.simple_filters = 'advertising/patch_note/other'
            # self.master_filters = 'arrangement/mixing/conduction/vocal/tune_vocal/instrumental/full_minus/copy_minus/turnkey_track/advertising/patch_note/other/special'
            self.tname = self.__class__.__name__.lower()
            result = self.test_connect()
            match result:
                case None:
                    return
                case False:
                    if not self.test_connect():
                        return
            self._structure:dict = getattr(self, '_table_struct')
            self.columns = [key for key in self._structure]
            self.columns.sort(key=lambda x: self._structure.get(x).pop('num'))
            for col in self.columns:
                if self._structure.get(col).get('iskey'):
                    self._rowid = col
                    break
            else:
                self._rowid = None
            self.columns_str = str(self.columns).replace("'", '')
            self.columns_temp = re.sub(r'[^,]*', '?', self.columns_str)
            # try:
            #     if self.tname == 'profiles':
            #         self.columns = ('id', 'username', 'first_name', 'last_name',
            #         'language_code', 'status', 'reputation', 'registered', 'nav', 'sys_lang', 'filters', '_unban_date')
            #     elif self.tname == 'orders':
            #         self.columns = ('id', 'customer', 'status', '_status_updated', 'type', 'master', 'description', 
            #                         'reference', 'product', 'deadline', '_logging', '_prev')
            #     elif self.tname == 'files':
            #         self.columns = ('id', 'order_id', 'path', 'bytes')
            #     elif self.tname == 'events':
            #         self.columns = ('id', 'time', 'code', 'regularity', 'exceptions', 'daemon', 'done', 'active')
        
        def test_connect(self):
            def getattr_(iterable):
                return getattr(*iterable)
            vals = ["_base_path", "_base_name", "_base_extension"]
            base_path, base_name, base_extension = map(getattr_, [(self, val, None) for val in vals])
            self.path = f"{base_path}{base_name}.{base_extension}"
            if not os.path.exists(self.path):
                logger.fatal(f"Base cannot connect to data: No such file in {self.path}")
                return
            try:
                sqlite3.connect(self.path)
                return True
            except Exception as e:
                logger.error(f"Base cannot connect to data: {e}")
                exc.tracebacking()
                return False
            
        def delete(self, id) -> bool:
            try:
                logger.debug(f"DELETE FROM {self.tname} WHERE id = {id}")
                self.execute(f"DELETE FROM {self.tname} WHERE id=?", (id,))
                return True
            except:
                return False
            
        def execute(self, request, values, /, timeout=None, ec=0):
            if timeout is None:
                timeout = getattr(self, "timeout", 5)
            try:
                with sqlite3.connect(self.path, timeout=timeout) as con:
                    cur = con.cursor()
                    result = cur.execute(request, values)
                    con.commit()
                return result
            except Exception as e:
                logger.warning(f"failed connection to {self._base_name} attempt: {e}")
                if ec <= 5:
                    self.execute(request, values)
                else:
                    logger.error(f"failed connection to {self._base_name} attempt")
        
        def fetch(self, id):
            data = self.execute(f"SELECT * FROM {self.tname} WHERE {self._rowid}=?", (id, ))
            data = data.fetchone()
                # if type(val) == bytes and autodecode:
                #     val = json.loads(val)
                # if not (val is None and ignore_nulls):
                #     answer.update({col: val})
            answer = self.generate(data)
            return answer

        def generate(self, data:tuple|None) -> dict:
            if data is None:
                return {None for _ in self.columns}
            else:
                return {key[int(key.startswith('_'))]: data[i] for i, key in enumerate(self.columns)}
        
        def get_default(self, col):
            info:dict = self._structure.get(col)
            return info.get("default")
        
        def insert(self, data:dict):
            values = tuple([data.get(col, self.get_default(col)) for col in self.columns])
            request = f"INSERT INTO profiles {self.columns_str} VALUES {self.columns_temp}"
            self.execute(request, values)

        def verify(self, id):
            if type(id) not in (int, str):
                return None
            id = self.execute(f"SELECT * FROM {self.tname} WHERE {self._rowid}=?", (id,))
            if id is None:
                return None
            return not id.fetchone() is None

        def search(self, what=None, sample:tuple=(), only_whole=True, column_wise=False) -> dict[dict[int]]|list:
            """Returns a dictionary with the keys 'whole' and 'part', which correspond to the lists of  table row 
            identifiers for full and partial matches with the variable 'what', respectively. The search is performed only 
            on the columns specified in the 'sample' variable, in case the variable is empty the search is 
            performed on all columns"""
            where = self.tname
            if sample == ():
                sample = self.columns
            elif type(sample) == str:
                sample = (sample, )
            result = {'whole': {"": []}, 'part': {"": []}}
            if what is None:
                column_wise = False
                whole = whole = self.execute(f"SELECT id FROM {where}", tuple())
                whole = [i[0] for i in whole.fetchall()]
                result.get('whole').update(self.add_result(result.get('whole'), whole))
                return whole
            for col in sample:
                if col not in self.columns:
                    continue
                match only_whole:
                    case 'past':
                        whole = self.execute(f"SELECT id FROM {where} WHERE {col}<?", (what, ))
                    case 'future':
                        whole = self.execute(f"SELECT id FROM {where} WHERE {col}>?", (what, ))
                    case _:
                        whole = self.execute(f"SELECT id FROM {where} WHERE {col}=?", (what, ))
                whole = [i[0] for i in whole.fetchall()]
                result.get('whole').update(self.add_result(result.get('whole'), whole, column_wise, col))
                if not only_whole:
                    part = self.execute(f"SELECT id FROM {where} WHERE {col} LIKE ?", (f"%{what}%",))
                    part = [i[0] for i in part.fetchall()]
                    result.get('part').update(self.add_result(result.get('part'), part, column_wise, col))
            return result

        def add_result(self, dictionary:dict, result:list, column_wise:bool=None, col:str=None)-> dict:
            first = dictionary.get('')
            first = list(set(first+result))
            dictionary.update({"": first})
            if not column_wise:
                return dictionary
            second = dictionary.get(col, [])
            second = list(set(second+result))
            dictionary.update({col: second})
            return dictionary

        def show(self, id_list=None) -> DataDict:
            answer = DataDict(self.tname, self.columns)
            if id_list is None:
                id_list = self.search()
            for ID in id_list:
                answer.add(self.fetch(ID))
            return answer

        def update(self, ID, request:dict):   
            for col, val in request.items():
                self._update(ID, col, val)
        
        def _update(self, ID, col, value):
            if not self.verify(ID):
                logger.warning(f"{self.tname} updating exception: No such rowid '{ID}'")
                return
            if col not in self.columns:
                logger.warning(f"{self.tname} updating exception: No such column '{col}'")
                return
            logger.debug(f"UPDATE profiles WHERE id = {ID} SET {col} = {value}")
            self.execute(f"UPDATE {self.tname} SET {col} =? WHERE id =?", (value, ID))

        

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
        logger.info(f"new profile, id={id}")
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


class Files(MetaBase.BasicBase, metaclass=MetaBase):
    def upload_file(self, file:dict) -> str:
        data = self.execute("SELECT id FROM files WHERE path= ?", (file.get('path'),)).fetchone()
        if data is None:
            ID = self.new_file(file)
        else:
            ID = data[0]
            self.update_file(ID, file)
        return ID
    
    def download_file(self, ID) -> bytes:
        file = self.fetch(ID, autodecode=False)
        return bz2.decompress(file.get("bytes", b''))
    
    def update_file(self, ID, request=dict):
        for col, val in request.items():
            if col not in self.columns:
                continue
            if col == "bytes":
                val = bz2.compress(val)
            self.execute(f"UPDATE files SET {col} =? WHERE id =?", (val, ID))
    
    def new_file(self, file: dict):
        order_id = file.get("order_id")
        path = file.get('path')
        file = bz2.compress(file.get('bytes'))
        ID = str(uuid.uuid4())
        while self.verify(ID):
            ID = str(uuid.uuid4())
        self.execute("INSERT INTO files (id, order_id, path, bytes) VALUES (?, ?, ?, ?)", 
                     (ID, order_id, path, file))
        return ID

    
    def update_event(self, ID, request:dict, /, autoencode:bool=True):
        for key, val in request.items():
            match key:
                case 'event':
                    ID = self.new_event(val)
                    return ID
                case _:
                    if key not in self.columns:
                        continue
            if type(val) not in {str, bytes, bool, int, float} and autoencode:
                try:
                    val = json.dumps(val).encode()
                except Exception as e:
                    logger.error(str(e))
            self.execute(f"UPDATE events SET {key} = ? WHERE id = ?", (val, ID))
        return ID


    def new_event(self, event:dict):
        ID = str(uuid.uuid4())
        while self.verify(ID):
            ID = str(uuid.uuid4())
        regularity = event.get('regularity')
        if type(regularity) is dict:
            regularity = clock.timedelta(**regularity).total_seconds()
        regularity = clock.try_int(regularity)
        event.update({"id": ID,
                      "regularity": regularity,
                      "time": event.get('time', '~'),
                      "code": event.get('code', 'test'),
                      "daemon": event.get('dayemon', 0),
                      "done": event.get('done', 0),
                      "active": event.get('active', 1)})
        values = tuple([event.get(key) for key in self.columns])
        self.execute(f"INSERT INTO events {self.columns} VALUES ({('?,'*len(self.columns))[:-1]})", values)
        return ID

    
class Orders(MetaBase.BasicBase, metaclass=MetaBase):
    def new_order(self, user:dict) -> int:
        suc = False
        while not suc:
            ID = random.randint(100000000, 999999999)
            suc = not self.verify(ID)
        data = {col: getattr(user, col, self.get_default(col)) for col in self.columns}
        clock.now()
        logger.debug(f"INSERT INTO orders new_order with id = {ID}")
        # self.execute("INSERT INTO orders (id, customer, status, _status_updated, reference, product, _logging) VALUES (?, ?, ?, ?, ?, ?, ?)",
        #     (
        #         ID,
        #         user['id'],
        #         "created",
        #         now,
        #         json.dumps({}).encode('utf-8'),
        #         json.dumps({}).encode('utf-8'),
        #         json.dumps({'created': now}).encode('utf-8')
        #     ))
        self.insert()
        return ID
    
    def update_order(self, ID, request=dict, hide_logs:bool=False, autoencode:bool=True):
        # if 'telegram_origin' in request:
        #     user = vars(request.pop('telegram_origin'))
        #     for col in user:
        #         if col in self.columns:
        #             self.update(id, col, user[col])
        for col in request.keys():
            val = request.get(col)
            if type(val) not in {str, bytes, bool, int, float} and autoencode:
                try:
                    val = json.dumps(val).encode()
                except Exception as e:
                    logger.error(f'{e}')
            if col not in self.columns:
                continue
            match col:
                case 'status':
                    self._update_order_status(ID, val)
                case _:
                    self.execute(f"UPDATE orders SET {col} =? WHERE id =?", (val, ID))
            if not hide_logs:
                logger.debug(f"UPDATE orders WHERE id = {ID} SET {col} = {request[col]}")


    def _update_order_status(self, ID, new_status) -> None:
        order = self.fetch(ID)
        status = order.get('status')
        if status in {'outdated', 'closed'}:
            logger.warning(f"order #{ID} was {status}, trying update status to {status}")
            return
        logging:dict = order.get('logging')
        status_updated = clock.now()
        logging.update({new_status: status_updated})
        logging = json.dumps(logging).encode()
        request = {"_logging": logging, "_status_updated": status_updated}
        self.update_order(ID, request, hide_logs=True)
        self.execute("UPDATE orders SET status =? WHERE id =?", (new_status, ID))

def getBase(name, *args, **kwargs)->MetaBase()|Profiles|Files|Orders|Events|Bytes|Logs:
    match name:
        case "Profiles":
            cls = Profiles
        case _:
            cls = MetaBase(name, tuple(args)+(MetaBase.BasicBase), kwargs)
    return cls()

if __name__ == "__main__":
    users_data:Profiles = getBase('Profiles')
    users_data.update_profile()
    users = getBase("Profiles")
    print(users_data, users)

    