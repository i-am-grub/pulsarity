"""
PropHazard server entry point
"""

import os
import sys
import multiprocessing
import logging
import logging.config
import logging.handlers

from . import prophazard_webserver
from .utils.config import configs

# pylint: disable=E0401

if sys.platform == "linux":
    multiprocessing.set_start_method("forkserver")
    from uvloop import run
elif sys.platform == "darwin":
    multiprocessing.set_start_method("spawn")
    from uvloop import run
elif sys.platform == "win32":
    multiprocessing.set_start_method("spawn")
    from winloop import run
else:
    multiprocessing.set_start_method("spawn")
    from asyncio import run


def _setup_logging():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    logging_conf = configs.get_section("LOGGING")
    if logging_conf is not None:
        logging.config.dictConfig(logging_conf)

        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None and isinstance(
            queue_handler, logging.handlers.QueueHandler
        ):
            queue_handler.listener.start()


def main() -> None:
    """
    Run the PropHazard server
    """
    _setup_logging()
    run(prophazard_webserver())


if __name__ == "__main__":
    main()
