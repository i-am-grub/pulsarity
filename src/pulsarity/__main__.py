"""
Pulsarity server entry point
"""

import logging
import logging.config
import os
import sys
import warnings

from pulsarity.utils.config import configs
from pulsarity.webserver import generate_webserver_coroutine

# pylint: disable=E0401

if sys.platform not in ("linux", "darwin"):
    from uvloop import run
else:
    from asyncio import run

    warnings.warn(
        "Attempting to run application with non-supported operating system",
        RuntimeWarning,
    )


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
