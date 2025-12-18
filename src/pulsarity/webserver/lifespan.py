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
from pulsarity.events import EventBroker, SpecialEvt
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.processor import RaceProcessorManager
from pulsarity.race.state import RaceStateManager
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


def set_context_vars() -> None:
    """
    Setup the default context variables for the
    application
    """

    ctx.loop_ctx.set(asyncio.get_running_loop())
    ctx.event_broker_ctx.set(EventBroker())
    ctx.race_state_ctx.set(RaceStateManager())
    ctx.race_processor_ctx.set(RaceProcessorManager())
    ctx.interface_manager_ctx.set(TimerInterfaceManager())


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    """
    Startup and shutdown procedures for the webserver

    :param _app: The application
    """

    logger.info("Starting Pulsarity...")
    set_context_vars()
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
    loop = ctx.loop_ctx.get()
    loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
    loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    ctx.interface_manager_ctx.get().start()

    await database_startup()

    await ctx.event_broker_ctx.get().trigger(SpecialEvt.STARTUP, {})


async def server_shutdown_workflow() -> None:
    """
    Shutdown workflow
    """
    event_broker = ctx.event_broker_ctx.get()
    await event_broker.trigger(SpecialEvt.SHUTDOWN, {})

    await ctx.interface_manager_ctx.get().shutdown(5)
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
