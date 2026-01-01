"""
Webserver event handling
"""

import asyncio
import contextlib
import json
import logging
import signal
from typing import Any, TypedDict

from starlette.applications import Starlette
from tortoise import Tortoise, connections

from pulsarity import ctx
from pulsarity.database import setup_default_objects
from pulsarity.events import EventBroker, SpecialEvt
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.manager import RaceManager
from pulsarity.race.processor import RaceProcessorManager
from pulsarity.utils import background
from pulsarity.utils.config import DEFAULT_CONFIG_FILE

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


class ContextState(TypedDict):
    """
    Context payload
    """

    loop: asyncio.AbstractEventLoop
    event: EventBroker
    race_state: RaceManager
    race_processor: RaceProcessorManager
    timer_inferface_manager: TimerInterfaceManager


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    """
    Startup and shutdown procedures for the webserver

    :param _app: The application
    """

    logger.info("Starting Pulsarity...")

    state = ContextState(
        loop=asyncio.get_running_loop(),
        event=EventBroker(),
        race_state=RaceManager(),
        race_processor=RaceProcessorManager(),
        timer_inferface_manager=TimerInterfaceManager(),
    )

    await server_starup_workflow(state)
    logger.info("Pulsarity startup completed...")

    yield state

    logger.info("Stopping Pulsarity...")
    await server_shutdown_workflow(state)
    logger.info("Pulsarity shutdown completed...")


async def server_starup_workflow(state: ContextState) -> None:
    """
    Startup workflow
    """
    await ctx.config_ctx.get().write_config_to_file_async(DEFAULT_CONFIG_FILE)

    loop = state["loop"]
    loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
    loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)

    token = ctx.loop_ctx.set(loop)
    state["timer_inferface_manager"].start()
    ctx.loop_ctx.reset(token)

    await database_startup()

    await state["event"].trigger(SpecialEvt.STARTUP, {})


async def server_shutdown_workflow(state: ContextState) -> None:
    """
    Shutdown workflow
    """
    await state["event"].trigger(SpecialEvt.SHUTDOWN, {})

    await state["timer_inferface_manager"].shutdown(5)
    await background.shutdown(5)
    await database_shutdown()


async def database_startup() -> None:
    """
    Initialize the database
    """
    await Tortoise.init(
        {
            "connections": ctx.config_ctx.get().database.model_dump(),
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
