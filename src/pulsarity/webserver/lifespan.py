"""
Webserver event handling
"""

import asyncio
import contextlib
import json
import logging
import signal
from typing import Any

from starlette.applications import Starlette
from tortoise import Tortoise, connections

from pulsarity import ctx
from pulsarity.database import setup_default_objects
from pulsarity.events import SpecialEvt, event_broker
from pulsarity.interface.timer_manager import interface_manager
from pulsarity.utils import background
from pulsarity.utils.config import configs

logger = logging.getLogger(__name__)

_shutdown_event = asyncio.Event()


def _signal_shutdown(*_: Any) -> None:
    """
    Set the event to shutdown the server gracefully
    """
    _shutdown_event.set()
    logger.debug("Server shutdown signaled")


async def shutdown_signaled() -> None:
    """
    Async function that waits until the server is
    signaled to shutdown
    """
    await _shutdown_event.wait()


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    """
    Startup and shutdown procedures for the webserver

    :param _app: The application
    """

    logger.info("Starting Pulsarity...")
    await server_starup_workflow()
    logger.info("Pulsarity startup completed...")

    yield

    logger.info("Stopping Pulsarity...")
    await server_shutdown_workflow()
    logger.info("Pulsarity shutdown completed...")


async def server_starup_workflow() -> None:
    """
    Startup workflow
    """
    loop = asyncio.get_running_loop()
    ctx.loop_ctx.set(loop)
    loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
    loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    interface_manager.start()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(database_startup())

    event_broker.trigger(SpecialEvt.STARTUP, {})


async def server_shutdown_workflow() -> None:
    """
    Shutdown workflow
    """
    event_broker.trigger(SpecialEvt.SHUTDOWN, {})

    await interface_manager.shutdown(5)
    await background.shutdown(5)
    await database_shutdown()


async def database_startup() -> None:
    """
    Initialize the database
    """
    await Tortoise.init(
        {
            "connections": configs.get_section("DATABASE"),
            "apps": {
                "system": {
                    "models": ["pulsarity.database"],
                    "default_connection": "system_db",
                },
                "event": {
                    "models": ["pulsarity.database"],
                    "default_connection": "event_db",
                },
            },
        }
    )

    await Tortoise.generate_schemas(True)
    await setup_default_objects()

    logger.debug("Database started, %s", json.dumps(tuple(Tortoise.apps)))


async def database_shutdown() -> None:
    """
    Shutdown the database
    """
    await connections.close_all()

    logger.debug("Database shutdown")
