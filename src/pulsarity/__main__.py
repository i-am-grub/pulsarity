"""
Pulsarity server entry point
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import granian
import pulsarity_localization
from granian.constants import Interfaces
from granian.log import LogLevels
from granian.server.embed import Server
from starlette.middleware.cors import CORSMiddleware

import pulsarity
from pulsarity.events.client import ClientServerRestart, ClientServerShutdown
from pulsarity.utils import config
from pulsarity.webserver import application

if TYPE_CHECKING:
    from starlette.types import ASGIApp

logger = logging.getLogger(__name__)
_shutdown_event = asyncio.Event()


def _signal_shutdown(*_) -> None:
    """
    Set the event to shutdown the server gracefully
    """
    _shutdown_event.set()
    logger.debug("Server shutdown signaled")


def _generate_server() -> Server:
    """
    Serve the Pulsarity application from a Granian server
    """
    configs = config.config_manager

    app: ASGIApp = application.generate_pulsarity_application()

    app = CORSMiddleware(
        app,
        allow_origins=configs.webserver.origins,
        allow_methods=("GET", "POST"),
        allow_headers=("Authorization", "Content-Type"),
    )

    return Server(
        app,
        address=configs.webserver.host,
        port=configs.webserver.port,
        interface=Interfaces.ASGI,
        log_level=LogLevels.info,
        log_dictconfig=configs.logging,
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

    logger.debug("Granian server version: %s", granian.__version__)
    logger.info("Pulsarity application version: %s", pulsarity.__version__)
    logger.info("Pulsarity Languages version: %s", pulsarity_localization.__version__)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server.serve())

        events: list[asyncio.Future] = [
            tg.create_task(ClientServerRestart.restart_evt.wait()),
            tg.create_task(ClientServerShutdown.shutdown_evt.wait()),
            tg.create_task(_shutdown_event.wait()),
        ]

        await asyncio.wait(events, return_when=asyncio.FIRST_COMPLETED)

        logger.info("Server shutdown signaled")

        for task in events:
            task.cancel()

        server.stop()

    logger.info("Server shutdown completed")


def main() -> None:
    """
    Run the default Pulsarity server
    """
    Path("logs").mkdir(exist_ok=True)

    asyncio.run(_server())

    if ClientServerShutdown.shutdown_evt.is_set():
        return

    if ClientServerRestart.restart_evt.is_set():
        logger.info("Automatically rebooting server")
        os.execv(sys.executable, [sys.executable, *sys.argv])  # noqa: S606


if __name__ == "__main__":
    main()
