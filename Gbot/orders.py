from .Gbot import GeorgeBot, exc, clock, tell, json

class OrdersMixin:
    @exc.protect
    def new_order(self:GeorgeBot, user:dict) -> int:
        ID = user['id']
        order_id = self.orders_data.new_order(user)
        match user['status']:
            case 'banned':
                return "banned"
            case 'newcomer':
                request = {'status': 'simple'}
                self.users_data.update_profile(ID, request)
        return order_id

    @exc.protect
    def ready_to_distribute(self:GeorgeBot, order_id:int, lang:str) -> tuple[str]:
        order = self.orders_data.fetch(order_id)
        ready = 'order_is_ready'
        columns = ''
        if not order.get('type'):
            ready = 'order_not_ready'
            t = tell('type_of_order', lang, ignore_all_insets=True)[:-2]
            columns += t+'\n'
        if not order.get('description'):
            ready = 'order_not_ready'
            t = tell('description_of_order', lang, ignore_all_insets=True)[:-2]
            columns += t+'\n'
        if clock.now('+1hour') >= order.get('deadline', '~'):
            ready = 'order_not_ready'
            t = tell('deadline_of_order', lang,  ignore_all_insets=True)[:-2]
            columns += t+'\n'
        return ready, columns

    @exc.protect
    def get_orders(self:GeorgeBot, /, customer:dict=None, master:dict=None)->dict:
        if customer is not None:
            c_id = customer.get('id')
            cust_orders = self.orders_data.search(c_id, ('customer',)).get('whole')['']
            id_set = set(cust_orders)
        if master is not None:
            m_id = master.get('id')
            mast_orders = self.orders_data.search(c_id, ('master',)).get('whole')['']
            id_set = set(mast_orders)
        if master and customer:
            id_set = set(cust_orders) & set(mast_orders)
        id_dict = {}
        for stat in self.orders_data.status_list:
            id_dict.update({stat: self.orders_data.search(stat, ('status',)).get('whole')['']})
        id_dict.update({"drafts": id_dict.pop('created') + id_dict.pop('recreated')})
        id_dict.update({"archive": id_dict.pop('closed')+id_dict.pop('completed')})
        for stat, id_list in id_dict.items():
            id_dict.update({stat: sorted(id_set & set(id_list), 
                                         key=lambda x: self.orders_data.peek(x, '_status_updated'),
                                         reverse=True)})
        return id_dict

    @exc.protect
    def get_services(self)->dict:
        with open("services.json", 'rb') as f:
            return json.load(f)
