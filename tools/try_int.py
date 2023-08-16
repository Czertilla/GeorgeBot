# import logging


def try_int(obj)-> int|None:
    try:
        return int(obj)
    except:
        return None
    
# logger = logging.getLogger(__name__)