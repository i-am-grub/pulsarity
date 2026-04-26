"""
Pulsarity server entry point
"""

import asyncio
import logging
import logging.config
import os
import signal
import sys

import pulsarity
from pulsarity.events.client import ClientServerRestart, ClientServerShutdown
from pulsarity.utils import config
from pulsarity.webserver import app

logger = logging.getLogger(__name__)
_shutdown_event = asyncio.Event()
_shutdown_setup_event = asyncio.Event()


def _setup_logging():
    """
    Setup the logging configuration for the server
    """

    if not os.path.exists("logs"):
        os.mkdir("logs")

    logging_conf = config.config_manager.logging
    if logging_conf is not None:
        logging.config.dictConfig(logging_conf)


def _signal_shutdown(*_) -> None:
    """
    Set the event to shutdown the server gracefully
    """
    _shutdown_event.set()
    logger.debug("Server shutdown signaled")


async def _setup_shutdown() -> None:
    """
    Await for the first shutdown event of the first
    time setup application to be set
    """

    waiters = [
        asyncio.create_task(_shutdown_event.wait()),
        asyncio.create_task(_shutdown_setup_event.wait()),
    ]
    await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)


async def _webserver_shutdown() -> None:
    """
    Await for the first shutdown event of the
    webserver application to be set
    """

    waiters = [
        asyncio.create_task(ClientServerRestart.restart_evt.wait()),
        asyncio.create_task(ClientServerShutdown.shutdown_evt.wait()),
        asyncio.create_task(_shutdown_event.wait()),
    ]
    await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)


async def _app() -> None:
    """
    Run the Pulsarity applications

    A first time setup application will be initally served if the
    config file is not present or parsable.

    The main application will be served after the first time setup
    check/setup
    """
    if sys.platform == "win32":
        signal.signal(signal.Signals.SIGINT, _signal_shutdown)
        signal.signal(signal.Signals.SIGTERM, _signal_shutdown)
    else:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
        loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    if not config.config_manager.from_save:
        logger.info("Starting first time setup application")
        setup_app = app.generate_setup_application(_shutdown_setup_event)
        coro = app.generate_webserver_coroutine(setup_app, _setup_shutdown)
        await coro
        logger.info("Stopped first time setup")

    if _shutdown_event.is_set():
        return

    app_ = app.generate_webserver_application()
    coro = app.generate_webserver_coroutine(app_, _webserver_shutdown)
    await coro


def main() -> None:
    """
    Run the default Pulsarity server
    """
    _setup_logging()
    logger.info("Server version: %s", pulsarity.__version__)

    asyncio.run(_app())

    if ClientServerShutdown.shutdown_evt.is_set():
        return

    if ClientServerRestart.restart_evt.is_set():
        logger.info("Automatically rebooting server")
        args = [sys.executable, "-m", "pulsarity", *sys.argv]
        os.execv(sys.executable, args)  # noqa: S606


if __name__ == "__main__":
    main()
