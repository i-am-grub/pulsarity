"""
Pulsarity server entry point
"""

import logging
import logging.config
import os
import sys
import warnings

import pulsarity
from pulsarity import ctx
from pulsarity.webserver import app

# pylint: disable=E0401

if sys.platform in ("linux", "darwin"):
    from uvloop import run
elif sys.platform == "win32":
    from winloop import run
else:
    from asyncio import run

    warnings.warn(
        (
            "The detected operating system does not support accelerated "
            "event loops; defaulting to the base event loop. Unexpected "
            "system behaviors may occur."
        ),
        RuntimeWarning,
    )


def _setup_logging():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    logging_conf = ctx.config_ctx.get().logging
    if logging_conf is not None:
        logging.config.dictConfig(logging_conf)


def main() -> None:
    """
    Run the default Pulsarity server
    """
    os.environ["REBOOT_PULSARITY_FLAG"] = "inactive"

    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Server version: %s", pulsarity.__version__)

    app_ = app.generate_webserver_application()
    coro = app.generate_webserver_coroutine(app_)
    run(coro)

    if os.environ["REBOOT_PULSARITY_FLAG"] == "active":
        logger.info("Automatically rebooting server")
        args = [sys.executable, "-m", "pulsarity", *sys.argv]
        os.execv(sys.executable, args)


if __name__ == "__main__":
    main()
