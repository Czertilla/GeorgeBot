from .base import *

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