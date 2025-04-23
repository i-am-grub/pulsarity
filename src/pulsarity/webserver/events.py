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

from ..database import setup_default_objects
from ..events import SpecialEvt, event_broker
from ..utils.background import background_tasks
from ..utils.config import configs
from ..utils.executor import executor

logger = logging.getLogger(__name__)

_shutdown_event = asyncio.Event()


def _signal_shutdown(*_: Any) -> None:
    """
    Set the event to shutdown the server gracefully
    """
    _shutdown_event.set()
    logger.debug("Server shutdown signaled")


async def shutdown_waiter() -> None:
    """
    Async function that awaits until the server is
    set to shutdown
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
    loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
    loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    executor.set_executor()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(database_startup())

    event_broker.trigger(SpecialEvt.STARTUP, {})


async def server_shutdown_workflow() -> None:
    """
    Shutdown workflow
    """
    event_broker.trigger(SpecialEvt.SHUTDOWN, {})

    await background_tasks.shutdown(5)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(executor.shutdown_executor())
        tg.create_task(database_shutdown())


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
