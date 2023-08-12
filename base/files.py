from .base import *

class Files(MetaBase.BasicBase,metaclass=MetaBase):
    def __init__(self):
        super().__init__()
        self._anchor_point = "folder"

    def download_file(self, file:dict) -> str:
        folder = self.hoist(file.get('folder'))
        info:dict
        for rowid, info in folder.items():
            if info.get('name') == file.get('name'):
                self.update_file(ID:=rowid, file)
                break
        else:
            ID = self.new_file(file)
        return ID
    
    def upload_file(self, ID) -> bytes:
        file = getBase("Bytedata").fetch(ID)
        return bz2.decompress(file.get("bytes", b''))
    
    def update_file(self, ID, request=dict):
        for col, val in request.items():
            if col not in self.columns:
                continue
            if col == "bytes":
                val = bz2.compress(val)
                getBase("Bytedata").update(ID, {"bytes": val})
            self.execute(f"UPDATE files SET {col} =? WHERE id =?", (val, ID))
    
    def new_file(self, file: dict):
        file_bytes = bz2.compress(file.pop('bytes'))
        ID = self.gen_id()
        file.update({"id": ID})
        self.insert(file)
        getBase("Bytedata").insert({"id": ID, 'bytes': file_bytes})
        return ID
