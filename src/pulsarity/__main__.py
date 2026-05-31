"""
Pulsarity server entry point
"""

import asyncio
import logging
import logging.config
import os
import signal
import sys

from granian.constants import Interfaces
from granian.log import LogLevels
from granian.server.embed import Server

import pulsarity
from pulsarity.events.client import ClientServerRestart, ClientServerShutdown
from pulsarity.utils import config
from pulsarity.webserver import application

logger = logging.getLogger(__name__)
_shutdown_event = asyncio.Event()


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


def _generate_server() -> Server:
    """
    Package the Pulsarity application into a Granian server
    """
    configs = config.config_manager

    app = application.generate_full_application()

    return Server(
        app,
        address=configs.webserver.host,
        port=configs.webserver.port,
        interface=Interfaces.ASGI,
        log_enabled=True,
        log_level=LogLevels.info,
        ssl_key=configs.webserver.key_file,
        ssl_cert=configs.webserver.cert_file,
        ssl_key_password=configs.webserver.key_password,
        ssl_ca=configs.webserver.ca_cert_file,
    )


async def _server() -> None:
    """
    The Pulsarity webserver coroutine.
    """
    if sys.platform == "win32":
        signal.signal(signal.Signals.SIGINT, _signal_shutdown)
        signal.signal(signal.Signals.SIGTERM, _signal_shutdown)
    else:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
        loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    server = _generate_server()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server.serve())

        events: list[asyncio.Future] = [
            asyncio.create_task(ClientServerRestart.restart_evt.wait()),
            tg.create_task(ClientServerShutdown.shutdown_evt.wait()),
            tg.create_task(_shutdown_event.wait()),
        ]

        pending: set[asyncio.Future]
        _, pending = await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        server.stop()


def main() -> None:
    """
    Run the default Pulsarity server
    """
    _setup_logging()
    logger.info("Server version: %s", pulsarity.__version__)

    asyncio.run(_server())

    if ClientServerShutdown.shutdown_evt.is_set():
        return

    if ClientServerRestart.restart_evt.is_set():
        logger.info("Automatically rebooting server")
        args = [sys.executable, "-m", "pulsarity", *sys.argv]
        os.execv(sys.executable, args)  # noqa: S606


if __name__ == "__main__":
    main()
