"""
Custom logging configs
"""

import logging.handlers


class AutoQueueListener(logging.handlers.QueueListener):
    """
    Auto starting Queue listener
    """

    def __init__(self, queue, *handlers, respect_handler_level=True):
        super().__init__(queue, *handlers, respect_handler_level=respect_handler_level)
        self.start()


def generate_default_config() -> dict:
    """
    Generates the default logging config for the server

    :return: The default dict config
    """

    return {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s]: %(message)s"},
            "detailed": {
                "format": "%(asctime)s [%(levelname)s|%(module)s|L%(lineno)d]: %(message)s",
                "datefmt": "%Y-%m%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "stderr": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": "INFO",
                "formatter": "detailed",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/prophazard.log",
                "when": "midnight",
                "interval": 1,
                "backupCount": 10,
            },
            "queue_handler": {
                "class": "logging.handlers.QueueHandler",
                "listener": "prophazard.utils.logging.AutoQueueListener",
                "handlers": ["stderr", "file"],
                "respect_handler_level": True,
            },
        },
        "loggers": {
            "root": {
                "handlers": ["queue_handler"],
                "level": "WARNING",
                "propagate": False,
            },
            "prophazard": {
                "handlers": ["queue_handler"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
