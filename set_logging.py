import logging.config

LOGGING = {
    "version": 1,
    # "disable_existing_loggers": True,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname}:{name}> {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard"
        },
        "filelog": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logFiles/debug.log",
            "mode": "a",
            "maxBytes": 4194304,
            "backupCount": 16,
            "formatter": "standard",
            "level": 'DEBUG'
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "__main__": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "exceptor": {
            "handlers": ["filelog"],
            "level": "ERROR",
            "propagate": False,
        },
        "Gbot": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "base": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": False,
        },
        "schedule": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "phrases": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "available_days": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "clock": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
        "last_mday": {
            "handlers": ["filelog"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

def config():
    logging.config.dictConfig(LOGGING)