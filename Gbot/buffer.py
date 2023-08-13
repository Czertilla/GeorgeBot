from .Gbot import logger

class Buffer(dict):
    def remove(self, chat_id):
        dict.update(self, {chat_id: self.get(chat_id, 0)-1})
        logger.debug(f'{self.get(chat_id)}(-1)')

    def update(self, chat_id):
        dict.update(self, {chat_id: self.get(chat_id, 0)+1})
        logger.debug(f'{self.get(chat_id)}(+1)')