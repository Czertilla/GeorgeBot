from exceptor import Exceptor
import json
import threading
import logging
"""27.6.2023 7:36:42"""
import time
from set_logging import LOGGING
# from Gbot import GeorgeBot
from base import Base
import clock
import datetime
import re

orders = Base('o')
users = Base('u')
files = Base('f')
events = Base('e')

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

logging.config.dictConfig(LOGGING)
log = logging.getLogger(__name__)

print(re.findall(r'[^#]*(?=#)', 'ban_menu#627784637#abusive_behavior'))

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

# def non_daemon():
#     logging.debug('Starting')
#     for i in range(20):
#         logging.debug(i)
#         time.sleep(0.1)
#     logging.debug('Exiting')
#     while True:
#         pass

# t = threading.Thread(name='non-daemon', target=non_daemon)

# d.start()
# t.start()
# for i in range(200):
#     logging.debug(i)
#     time.sleep(0.1)
# d.join()

a = datetime.datetime.strptime(clock.now(), '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(clock.now('+3seconds'), '%Y-%m-%d %H:%M:%S')
print(a.total_seconds())
