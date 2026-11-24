"""Pulsarity server entry point."""

import asyncio
import logging
import os
import platform
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
from pulsarity._core import ctx
from pulsarity._core.events import EventBroker
from pulsarity._core.race.manager import RaceManager
from pulsarity._core.timing_interface.timer_manager import TimerInterfaceManager
from pulsarity._core.utils import config
from pulsarity._core.webserver import application

if TYPE_CHECKING:
    from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class PulsarityServer(Server):
    """Pulsarity ASGI webserver."""

    async def shutdown_server(self):
        """Cleanly shutdown the webserver.

        This method will shutdown parts of the server
        that can not be cleaned up before the
        Granian server is signalled to shutdown.
        """
        await ctx.ws_conn_tracker.wait_all_closed()
        self.stop()


def _signal_shutdown(*_) -> None:
    """Set the event to shutdown the server gracefully."""
    ctx.shutdown_app.set()
    logger.debug("Server shutdown signaled")


def _generate_server() -> PulsarityServer:
    """Serve the Pulsarity application from a Granian server."""
    configs = config.config_manager

    app: ASGIApp = application.generate_pulsarity_application()

    app = CORSMiddleware(
        app,
        allow_origins=configs.webserver.origins,
        allow_methods=("GET", "POST"),
        allow_headers=("Authorization", "Content-Type"),
    )

    return PulsarityServer(
        app,
        address=configs.webserver.host,
        port=configs.webserver.port,
        interface=Interfaces.ASGI,
        log_level=LogLevels.info,
        log_dictconfig=config.generate_logging_config(configs.general.debug),
        ssl_key=configs.webserver.key_file,
        ssl_cert=configs.webserver.cert_file,
        ssl_key_password=configs.webserver.key_password,
        ssl_ca=configs.webserver.ca_cert_file,
    )


async def _server() -> None:
    """The Pulsarity webserver coroutine."""
    ctx.evt_loop = loop = asyncio.get_running_loop()

    if sys.platform == "win32":
        signal.signal(signal.Signals.SIGINT, _signal_shutdown)
        signal.signal(signal.Signals.SIGTERM, _signal_shutdown)
    else:
        loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
        loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    logger.info("Platform: %s", platform.platform())
    logger.info("CPU count: %s", os.cpu_count())
    logger.info("Python: %s", platform.python_version())
    logger.info("GIL enabled: %s", sys._is_gil_enabled())
    logger.info("JIT enabled: %s", sys._jit.is_enabled())
    logger.debug("Granian server: %s", granian.__version__)
    logger.info("Pulsarity application: %s", pulsarity.__version__)
    logger.info("Pulsarity localization: %s", pulsarity_localization.__version__)

    server = _generate_server()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server.serve())

        await ctx.shutdown_app.wait()

        logger.info("Server shutdown signaled")

        await server.shutdown_server()

    logger.info("Server shutdown completed")


def main() -> None:
    """Run the default Pulsarity server."""
    Path("logs").mkdir(exist_ok=True)

    ctx.event_broker = EventBroker()
    ctx.race_manager = RaceManager()
    ctx.timer_manager = TimerInterfaceManager()

    asyncio.run(_server())

    if ctx.restart_app:
        logger.info("Automatically rebooting server")
        os.execv(sys.executable, [sys.executable, *sys.argv])  # noqa: S606


if __name__ == "__main__":
    main()
