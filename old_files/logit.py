from tools.clock import now
import logging

logger = logging.getLogger(__name__)

def logit(*args, end='\n', cont=False):
    if cont:
        print(*args, end=end)
    else:
        print(now(), *args, end=end)
    # message = ' '.join(map(str, args))
    # logging.info(message)

if __name__ == "__main__":
    logit(input())