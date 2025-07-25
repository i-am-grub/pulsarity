"""
Pulsarity server entry point
"""

import logging
import logging.config
import multiprocessing
import os
import sys

from pulsarity.utils.config import configs
from pulsarity.webserver import generate_webserver_coroutine

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


def main() -> None:
    """
    Run the default Pulsarity server
    """
    multiprocessing.freeze_support()

    os.environ["REBOOT_PULSARITY_FLAG"] = "inactive"

    _setup_logging()
    logger = logging.getLogger(__name__)

    coro = generate_webserver_coroutine()
    run(coro)

    if os.environ["REBOOT_PULSARITY_FLAG"] == "active":
        logger.info("Automatically rebooting server")
        args = [sys.executable, "-m", "pulsarity", *sys.argv]
        os.execv(sys.executable, args)


if __name__ == "__main__":
    main()
