from .base import *

class Orders(MetaBase.BasicBase, metaclass=MetaBase):
    def __init__(self)->None:
        super().__init__()
        self.status_list = ['created', 
                            'distributed', 
                            'proposed',
                            'accepted',
                            # 'unpaid',
                            # 'paid',
                            'completed',
                            'recreated',
                            'closed']
        self._set_anchor("reference", "Files")
        self._set_anchor("_logging", "Logs")
        # self._set_anchor("product", "Files")
    
    def peek(self, ID, column):
        if column not in self.columns:
            return
        result = self.execute(f"SELECT {column} FROM {self.tname} WHERE {self._rowid}=?", (ID, ))
        return result.fetchone()[0]

    def orders_limit(self, user_id) -> bool:
        id_list = self.execute(
            f"SELECT id FROM {self.tname} WHERE customer = ? AND NOT status = 'closed' AND NOT status = 'comleted'",
            (user_id,))
        return len(id_list.fetchall()) >= 10

    def new_order(self, user:dict) -> int:
        if self.orders_limit(user.get('id')):
            return 'too many'
        ID = random.randint(100000000, 999999999)
        while self.verify(ID):
            ID = random.randint(100000000, 999999999)
        customer = user.get('id')
        data = {"_status_updated":(now:=clock.now()), 
                     'id': ID, 
                     'customer': customer,
                     'reference':f"{ID}/reference",
                     'product':f'{ID}/product', '_logging': f'{ID}/logging'}
        logger.debug(f"INSERT INTO orders new_order with id = {ID}")
        self.insert(data)
        self._update_order_status(ID, "created", date=now)
        return ID
    
    def update_order(self, ID, request=dict, hide_logs:bool=False, autoencode:bool=True):
        reference = request.pop('reference', None)
        product = request.pop('product', None)
        status = request.pop('status', None)
        if status:
            self._update_order_status(ID, status)
        self.update(ID, request)

    def delete(self, ID:int) -> bool:
        subtable:Files = getBase('Files')
        id_list = subtable.search(f"{ID}/", 
                                  sample=('folder',), 
                                  only_whole=False).get('part')['']
        for f_id in id_list:
            subtable.delete(f_id)
        return super().delete(ID)

    def _update_order_status(self, ID, new_status, /, date=None) -> None:
        order = self.fetch(ID)
        status = order.get('status')
        if status in {'outdated', 'closed'}:
            logger.warning(f"order #{ID} was {status}, trying update status to {new_status}")
            return
        subtable:Logs = Logs()
        if date is None:
            status_updated = clock.now()
        else:
            status_updated = date
        subtable.new_log(f"{ID}/logging", new_status, status_updated)
        request = {"status": new_status, "_status_updated": status_updated}
        self.update(ID, request)
