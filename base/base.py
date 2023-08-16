import logging
import re
import sqlite3
import os
import tools.clock as clock
import phrases
import random
import uuid
import bz2
from exceptor import Exceptor

logger = logging.getLogger(__package__)
exc = Exceptor()

from base.datadict import DataDict


class MetaBase(type):
    _exception = object()
    _instance_dict = {}
    _anchor_point = "anchor"
    _base_path = '\\'.join(__file__.split('\\')[:-2]+['db'])+'\\'
    _base_name = "data"
    _base_extension = "db"
    def __new__(cls, name, bases, attrs:dict={}):
        table_info = cls.get_table_info(name)
        if table_info is None:
            return
        namespace = {"_table_struct": table_info,
                     "_anchor_point": cls._anchor_point,
                     "_exception": cls._exception,
                     "_base_path": cls._base_path,
                     "_base_name": cls._base_name,
                     "_base_extension": cls._base_extension,
                     }
        namespace.update(**attrs)
        return super(MetaBase, cls).__new__(cls, name, (cls.BasicBase,), namespace)

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
        def get_dflt(sql_val, py_type:object):
            if sql_val is None:
                return
            if py_type == type('') and sql_val[0] == sql_val[-1] == "'":
                return sql_val[1:-1]
            return py_type(sql_val)
        if (_tnames:=getattr(MetaBase, '_tnames', meta.get_base_names())) is None:
            return
        if name not in _tnames:
            return
        info = meta.BasicBase.execute(meta, f"PRAGMA table_info({name})", ()).fetchall()
        table_info = {col[1]: {
                "num": col[0],
                "type": (t:=get_type(col[2])),
                "not_NULL": bool(col[3]),
                "default": get_dflt(col[4], t),
                "iskey": bool(col[5])
            } for col in info}
        return table_info

    @classmethod
    def get_base_names(meta): 
        names = meta.BasicBase.execute(meta, "SELECT name FROM sqlite_master WHERE type='table'", ())
        if names is None:
            return
        names = names.fetchall()
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
            self.columns_str = str(tuple(self.columns)).replace("'", '')
            self.columns_temp = re.sub(r'(?<=\(| )[^(),]*(?=\)|,)', '?', self.columns_str)

        def test_connect(self):
            path = f"{self._base_path}{self._base_name}.{self._base_extension}"
            if not os.path.exists(path):
                logger.fatal(f"Base cannot connect to data: No such file in {path}")
                return
            try:
                sqlite3.connect(path)
                return True
            except Exception as e:
                logger.error(f"Base cannot connect to data: {e}")
                exc.tracebacking()
                return False
            
        def delete(self, ID) -> bool:
            try:
                logger.debug(f"DELETE FROM {self.tname} WHERE id = {ID}")
                self.execute(f"DELETE FROM {self.tname} WHERE id=?", (ID,))
                return True
            except:
                return False
            
        def execute(self, request, values, /, timeout=None, ec=0):
            if timeout is None:
                timeout = getattr(self, "timeout", 5)
            try:
                path = f"{self._base_path}{self._base_name}.{self._base_extension}"
                with sqlite3.connect(path, timeout=timeout) as con:
                    cur = con.cursor()
                    result = cur.execute(request, values)
                    con.commit()
                return result
            except Exception as e:
                logger.debug(f"failed connection to {self._base_name} attempt: {e}")
                if ec <= 5 and getattr(self, "execute", False):
                    self.execute(request, values, ec=ec+1)
                else:
                    logger.error(f"failed connection to {self._base_name} attempt")
        
        def fetch(self, ID):
            data = self.execute(f"SELECT * FROM {self.tname} WHERE {self._rowid}=?", (ID, ))
            data = data.fetchone()
                # if type(val) == bytes and autodecode:
                #     val = json.loads(val)
                # if not (val is None and ignore_nulls):
                #     answer.update({col: val})
            answer = self.generate(data)
            return answer

        def generate(self, data:tuple|None) -> dict:
            if data is None:
                return {col:None for col in self.columns}
            sturcture = self._structure
            result = {}
            for i, col in enumerate(self.columns):
                info:dict = sturcture.get(col)
                if subt := info.get('anchor'):
                    subtable = getBase(subt)
                    val = subtable.hoist(data[i])
                else:
                    val = data[i]
                result.update({col[int(col.startswith('_')):]: val})
            return result
        
        def gen_id(self):
            ID = str(uuid.uuid4())
            while self.verify(ID):
                ID = str(uuid.uuid4())
            return ID

        def get_default(self, col):
            info:dict = self._structure.get(col)
            dfl = info.get("default")
            if dfl is None:
                return dfl
            cls = info.get('type')
            return cls(dfl)
        
        def hoist(self, anchor):
            col = self._anchor_point
            if col not in self.columns:
                logger.error(f"hoisting from <<{self.tname}>> exception: No such anchor-column <{col}>")
                return {}
            id_list = self.execute(f"SELECT id FROM {self.tname} WHERE {col}=?", (anchor,))
            result = {}
            if id_list is None:
                return result
            id_list = id_list.fetchall()
            for ID in id_list:
                row = self.fetch(ID[0])
                row_id = row.pop(self._rowid)
                if row is not None:
                    row.pop(col)
                result.update({row_id: row})
            return result
        
        def insert(self, data:dict):
            values = []
            for col in self.columns:
                if not self._parse(col, val:=data.get(col, self.get_default(col))):
                    logger.error(f"{data} have not inserted in <<{self.tname}>>")
                    return
                values.append(val)
            values = tuple(values)
            request = f"INSERT INTO {self.tname} {self.columns_str} VALUES {self.columns_temp}"
            self.execute(request, values)

        def verify(self, ID):
            if type(ID) not in (int, str):
                return None
            ID = self.execute(f"SELECT * FROM {self.tname} WHERE {self._rowid}=?", (ID,))
            if ID is None:
                return None
            return not ID.fetchone() is None
        
        def _set_anchor(self, col:str, subtable:str|None=None):
            info:dict = self._structure.get(col)
            if info is None:
                return
            if getBase(subtable) is None:
                return
            info.update({'anchor': subtable})
            
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
        
        def _parse(self, column, value)->bool:
            info:dict = self._structure.get(column)
            head = f"Parse inadequating <{column}> in <<{self.tname}>>"
            if info is None:
                logger.warning(f"{head}: No such information about <<{column}>> column")
                return False
            if value is None and info.get('not_NULL'):
                logger.warning(f"{head}: NoneType value in not_NULL column <{column}>")
                return False
            if (v:= type(value)) != (c:=info.get('type')) and value is not None:
                logger.warning(f"{head}: type inadequating ({v} -> {c})")
                return False
            return True 

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
            if not self._parse(col, value):
                logger.warning(f"{self.tname} updating exception: value inadequate during parsing")
                return
            logger.debug(f"UPDATE {self.tname} WHERE id = {ID} SET {col} = {value}")
            self.execute(f"UPDATE {self.tname} SET {col} =? WHERE id =?", (value, ID))

from base.profiles import Profiles

from base.files import Files

from base.events import Events

from base.orders import Orders

from base.logs import Logs


def getBase(name, *args, **kwargs)->MetaBase.BasicBase|Profiles|Files|Orders|Events|Logs:
    match name:
        case "Profiles":
            cls = Profiles
        case "Files":
            cls = Files
        case "Orders":
            cls = Orders
        case "Logs":
            cls = Logs
        case _:
            cls = MetaBase(name, tuple(args), kwargs)
    if cls is None:
        return
    return cls()

if __name__ == "__main__":
    files_data:Files = getBase("Files")
    orders_data:Orders = getBase("Orders")
    orders_data.delete(577812096)
    