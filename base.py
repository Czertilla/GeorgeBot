import logging
import sqlite3

import json
import pickle
import clock
import phrases
import random
import uuid
import bz2

logger = logging.getLogger(__name__)

class DataDict(dict):
    def __init__(self,name,colums, *args, **kwargs):
        self.name = name
        self.date = clock.now()
        self.colums = colums
        self.set_width()
        dict.__init__(self, *args, **kwargs)
    def set_width(self):
        self.row_width = max(len(max(self.colums, key=lambda x: len(x))) + 2, 77/len(self.colums))
    def __add__(self, other):
        dict.update(self, other)
        return self
    def add(self, D:dict):
        self.update(D)
    def update(self, D:dict):
        dict.update(self, {D.pop('id'): D})
    def __str__(self):
        result = f"@{self.name:20s} %{self.date}\n"
        for key in self.colums:
            result += f"{key:{self.row_width}}"
        result += f'\n{"="*self.row_width*len(self.colums)}\n'
        for key, record in self.items():
            result += f"{str(key):{self.row_width}.{self.row_width}}"
            for col in self.colums[1:]:
                result += f"{str(record.get(col)):{self.row_width}.{self.row_width}}"
            result += f'\n{"_"*self.row_width*len(self.colums)}\n'
        return result

class Base:
    def __init__(self, code, outer=None):
        self.exceptions_stack = []
        self.exceptions_count = 0
        self.simple_filters = 'advertising/patch_note/other'
        self.master_filters = 'arrangement/mixing/conduction/vocal/tune_vocal/instrumental/full_minus/copy_minus/turnkey_track/advertising/patch_note/other/special'
        self.mode = {'u': "profiles", 'o': "orders", 'f': "files", 'e': "events"}[code]
        self.outer = outer
        try:
            if self.mode == 'profiles':
                self.colums = ('id', 'username', 'first_name', 'last_name',
                'language_code', 'status', 'reputation', 'registered', 'nav', 'sys_lang', 'filters', '_unban_date')
                self.base_name = 'users'
                # self.con = sqlite3.connect("db/users.db", check_same_thread=False)
            elif self.mode == 'orders':
                self.colums = ('id', 'customer', 'status', '_status_updated', 'type', 'master', 'description', 
                               'reference', 'product', 'deadline', '_logging', '_prev')
                self.base_name = 'users'
                # self.con = sqlite3.connect("db/games.db", check_same_thread=False)
            elif self.mode == 'files':
                self.colums = ('id', 'order_id', 'path', 'bytes')
                self.base_name = 'users'
            elif self.mode == 'events':
                self.colums = ('id', 'time', 'code', 'regularity', 'exceptions', 'daemon', 'done', 'active')
                self.base_name = 'users'
        except Exception as e:
                return f"An attempt to connect to the database {self.mode} failed: \n\t {e}" 

    def execute(self, request, values):
        try:
            with sqlite3.connect(f"db/{self.base_name}.db", timeout=30) as con:
                cur = con.cursor()
                result = cur.execute(request, values)
                con.commit()
            return result
        except Exception as e:
            if len(self.exceptions_stack) == 0:
                exceptions_count = 1
            elif str(e) == self.exceptions_stack[-1]:
                self.exceptions_count += 1
            else:
                self.exceptions_count = 0
            self.exceptions_stack.append(str(e))
            logger.warning(f"failed connection to {self.base_name} attempt: {e}")
            if self.exceptions_count <= 20:
                self.execute(request, values)
            else:
                logger.error(f"failed connection to {self.base_name} attempt")

    def fetch(self, id, autodecode:bool=True, ignore_nulls:bool=False):
        data = self.execute(f"SELECT * FROM {self.mode} WHERE id=?", (id, ))
        data = data.fetchone()
        if data is None and not ignore_nulls:
            answer = {col: None for col in self.colums}
            answer['status'] = 'unknow'
            logger.warning(f"in {self.mode} data unknow id: {id}")
            return answer
        elif data is None and ignore_nulls:
            logger.warning(f"in {self.mode} data unknow id: {id}")
            answer = {'status': 'unknow'}
            return answer
        answer = {}
        r = 0
        for r, col in enumerate(self.colums):
            val = data[r]
            if col[0] == '_':
                col = col[1:]
            if type(val) == bytes and autodecode:
                val = json.loads(val)
            if not (val is None and ignore_nulls):
                answer.update({col: val})
        return answer

    def delete(self, id) -> bool:
        try:
            logger.debug(f"DELETE FROM {self.mode} WHERE id = {id}")
            self.execute(f"DELETE FROM {self.mode} WHERE id=?", (id,))
            return True
        except:
            return False
    
    def search(self, what=None, sample:tuple=(), only_whole=True, column_wise=False) -> dict[dict[int]]|list:
        """
Returns a dictionary with the keys 'whole' and 'part', which correspond to the lists of  table row 
identifiers for full and partial matches with the variable 'what', respectively. The search is performed only 
on the columns specified in the 'sample' variable, in case the variable is empty the search is 
performed on all columns
        """
        where = self.mode
        if sample == ():
            sample = self.colums
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
            if col not in self.colums:
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
        answer = DataDict(self.mode, self.colums)
        if id_list is None:
            id_list = self.search()
        for ID in id_list:
            answer.add(self.fetch(ID))
        return answer



    def generate(self, data:tuple) -> list:
        answer = {}
        for i, key in enumerate(self.colums):
            answer.update({key: data[i]})
        return answer
    
    def generateall(self, data:list[tuple]) -> list[dict]:
        pass
    
    def update(self, id, col, value):
        if col not in self.colums:
            return
        self.execute(f"UPDATE {self.mode} SET {col} =? WHERE id =?", (value, id))

    def verify(self, id):
        loc = self.mode
        if type(id) not in (int, str):
            return None
        id = self.execute(f"SELECT * FROM {loc} WHERE id=?", (id,))
        if id is None:
            return None
        return not id.fetchone() is None
    
    def check_access_lvl(self, id, lvl=0):
        user = self.fetch(id)
        if lvl >= 100:
            return user["status"] == "god"
        if lvl >= 10:
            return user["status"] != "bunned"

    #only profiles
    def sign_in(self, user):
        if self.verify(user.id):
            self.update_profile(user.id, {'user': user, 'nav': 'main_menu'})
            return phrases.tell('welcome_back', user.language_code, {'name': user.first_name})
        else:
            self.new_profile(user)
            return phrases.tell('welcome', user.language_code, {'name': user.first_name})
    
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
            if col not in self.colums:
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


    def update_old_date(self, ID):
        data = self.fetch(ID)
        log:dict = data.get('logging')
        for key in log.keys():
            date = clock.package(log.get(key), gradation='normal', ignore_nulls=True)
            year = date.get('year')
            if year is None:
                return
            month = date.get('month', 99)
            day = date.get('day', 99)
            hour = date.get('hour', 99)
            min = date.get('minute', 99)
            sec = date.get('second', 99)
            log.update({key: f"{year:04}-{month:02}-{day:02} {hour:02}:{min:02}:{sec:02}"})
            if year is None:
                log.update({key: '~'})
        request = {'logging': json.dumps(log).encode()}
        self.update_order(ID, request)
    
    def update_event(self, ID, request:dict, /, autoencode:bool=True):
        for key, val in request.items():
            match key:
                case 'event':
                    ID = self.new_event(val)
                    return ID
                case _:
                    if key not in self.colums:
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
        event.update({"id": ID,
                      "time": event.get('time', '~'),
                      "code": event.get('code', 'test'),
                      "daemon": event.get('dayemon', 0),
                      "done": event.get('done', 0),
                      "active": event.get('active', 1)})
        values = tuple([event.get(key) for key in self.colums])
        self.execute(f"INSERT INTO events {self.colums} VALUES ({('?,'*len(self.colums))[:-1]})", values)
        return ID

    #only profiles
    def new_profile(self, user):
        id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        language_code = user.language_code
        if not language_code in phrases.language_codes:
            language_code = 'en'
        registered = clock.now()
        if id == 715648962:
            status = "god"
        else:
            status = "newcomer"
        logger.info(f"new profile, id={id}")
        self.execute("INSERT INTO profiles (id, username, first_name, last_name,\
            language_code, status, reputation, registered) VALUES \
            (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                id, 
                username, 
                first_name, 
                last_name, 
                language_code,
                status, 
                0.0, 
                registered
            ))
    
    
    #only profiles    
    def update_profile(self, id, request=dict):
        if 'user' in request:
            user = vars(request.pop('user'))
            for col in user:
                if col in self.colums:
                    self.update(id, col, user[col])
        for col in request.keys():
            logger.debug(f"UPDATE profiles WHERE id = {id} SET {col} = {request[col]}")
            self.execute(f"UPDATE profiles SET {col} =? WHERE id =?", (request[col], id))
        reputation = self.fetch(id)['reputation']
        status = self.fetch(id)['status']
        if status == 'unknow':
            return
        
    #only profiles
    def discard_profile(self, id):
        if id == 715648962:
            return "БОГ БЕССМЕРТЕН"
        self.execute("DELETE FROM profiles WHERE id =?", (id, ))
    
    #only orders
    def new_order(self, user:dict) -> int:
        suc = False
        while not suc:
            ID = random.randint(100000000, 999999999)
            suc = not self.verify(ID)
            now = clock.now()
        logger.debug(f"INSERT INTO orders new_order with id = {ID}")
        self.execute("INSERT INTO orders (id, customer, status, _status_updated, reference, product, _logging) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                ID,
                user['id'],
                "created",
                now,
                json.dumps({}).encode('utf-8'),
                json.dumps({}).encode('utf-8'),
                json.dumps({'created': now}).encode('utf-8')
            ))
        return ID
    
    #only sessions
    def update_order(self, ID, request=dict, hide_logs:bool=False, autoencode:bool=True):
        # if 'telegram_origin' in request:
        #     user = vars(request.pop('telegram_origin'))
        #     for col in user:
        #         if col in self.colums:
        #             self.update(id, col, user[col])
        for col in request.keys():
            val = request.get(col)
            if type(val) not in {str, bytes, bool, int, float} and autoencode:
                try:
                    val = json.dumps(val).encode()
                except Exception as e:
                    logger.error(f'{e}')
            if col not in self.colums:
                continue
            match col:
                case 'status':
                    self._update_order_status(ID, val)
                case _:
                    self.execute(f"UPDATE orders SET {col} =? WHERE id =?", (val, ID))
            if not hide_logs:
                logger.debug(f"UPDATE orders WHERE id = {ID} SET {col} = {request[col]}")
        # order = self.fetch(id)
        # closed = ses['closed']
        # status = ses['status']
        # if closed != None and status != 'closed':
        #     self.update_session(id, {'status': 'closed'})
        #     logger.debug(f"Some problem with data have detected during checking session:{ses['id']} status, need to check")
        #     if self.outer is None:
        #         return None
        #     self.outer.problems += 1
        # elif closed == None and status == 'closed':
        #     logger.debug(f"Some problem with data have detected during checking session:{ses['id']} status")
        #     if self.outer is None:
        #         return None
        #     self.outer.problems += 1

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


if __name__ == "__main__":
    debug = Base("u")
    debug.fetch(715648962)

    