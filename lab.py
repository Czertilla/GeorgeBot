import sqlite3
from exceptor import Exceptor
import json
import threading
import logging
"""27.6.2023 7:36:42"""
import time
from set_logging import LOGGING
from Gbot import GeorgeBot
import base
import clock
import datetime
import re
"Запись. аранжировка. сведение. трек под ключ. копия минуса. Особое"
# orders = Base('o')
# users = Base('u')
# files = Base('f')
# events = Base('e')

import logging
# from tqdm import trange
# from tqdm.contrib.logging import logging_redirect_tqdm

# LOG = logging.getLogger(__name__)

# if __name__ == '__main__':
#     logging.basicConfig(level=10, format="%(asctime)s %(levelname)s:%(name)s:%(lineno)s> %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
#     with logging_redirect_tqdm():
#         for i in trange(9):
#             if i == 4:
#                 LOG.info("console logging redirected to `tqdm.write()`")
    # logging restored

# logging.basicConfig(level=logging.INFO,
#                     format='(%(threadName)-10s) %(message)s',
#                     )
import logging.config

# bot = GeorgeBot("5990727623:AAHbJxQ-dnVZoZ4lmm9bxXXPlwQIbVtIKW0", users, orders)


# def daemon():
#     logging.debug('Starting')
#     time.sleep(2)
#     d = threading.Thread(name='non-daemon_in-daemon', target=non_daemon)
#     d.start()
#     for i in range(100):
#         logging.debug(i)
#         time.sleep(0.1)
#     d.join()
#     logging.debug('Exiting')

# d = threading.Thread(name='daemon', target=daemon)
# d.setDaemon(True)


execute = base.MetaBase.BasicBase.execute

a = re.sub(r'(?<=\(| )[^(),]*(?=\)|,)', '?', '(id, tg_id, f_name, path, order_id, bytes)')
print(a)










class A:
    a = 0

b = A()
c = b.a
A.a = 1
print(c)
print(b.a)
# t = threading.Thread(name='non-daemon', target=non_daemon)

# d.start()
# t.start()
# for i in range(200):
#     logging.debug(i)
#     time.sleep(0.1)
# d.join()

# a = datetime.datetime.strptime(clock.now(), '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(clock.now('+3seconds'), '%Y-%m-%d %H:%M:%S')
# print(a.total_seconds())
