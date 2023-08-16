from constants import *
import sys
import logging
from tools.get_version import get_version
import logging.config



logger = logging.getLogger(__name__)

from admin import Admin

if __name__ == "__main__":
    # logger = get_log_config()
    # logging.basicConfig(format="%(asctime)s %(levelname)s:%(name)s:%(lineno)s> %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
    from tools.set_logging import config
    config()
    ver = get_version()
    logger.info(f"{f'{ver:10s}'.replace(' ', '=')}============ session started =======================")
    administrator = Admin()
    for command in sys.stdin:
        administrator._command_exec(command)
        if administrator.closed:
            break
