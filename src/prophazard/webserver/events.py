"""
Webserver event handling
"""

import logging
import asyncio
import signal
from typing import Any

from quart import ResponseReturnValue, redirect, url_for
from quart_auth import Unauthorized

from ..extensions import RHBlueprint, current_app
from ..events import SpecialEvt

from ..database.user import UserDatabaseManager
from ..database.race import RaceDatabaseManager

from ..utils.executor import executor
from ..utils.config import configs

logger = logging.getLogger(__name__)

p_events = RHBlueprint("private_events", __name__)
events = RHBlueprint("events", __name__)

shutdown_event = asyncio.Event()


def _signal_shutdown(*_: Any) -> None:
    """
    Trigger the event to shutdown the server
    """
    logger.info("Shutting down server...")
    shutdown_event.set()


@p_events.before_app_serving
async def register_shutdown_signals() -> None:
    """
    Registers signals to trigger signal shutdown
    """
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
    loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)


@events.while_app_serving
async def lifespan() -> Any:
    """
    Trigger startup and shutdown events
    """
    current_app.event_broker.trigger(SpecialEvt.STARTUP, {})
    yield
    current_app.event_broker.trigger(SpecialEvt.SHUTDOWN, {})


@events.errorhandler(Unauthorized)
async def redirect_to_index(*_) -> ResponseReturnValue:
    """
    Redirects the user when `Unauthorized` to access
    a route or websocket

    :return: The server response
    """
    return redirect(url_for("index"))


@events.before_app_serving
async def setup_global_executor() -> None:
    """
    Sets executor to uses for computationally intestive
    processing.
    """
    executor.set_executor()


@p_events.before_app_serving
async def setup_user_database() -> None:
    """
    Sets the active user database for the server
    """

    database_manager = UserDatabaseManager(filename="user.db")
    await database_manager.setup()

    default_username = str(configs.get_config("SECRETS", "DEFAULT_USERNAME"))
    default_password = str(configs.get_config("SECRETS", "DEFAULT_PASSWORD"))

    await database_manager.verify_persistant_objects(default_username, default_password)

    current_app.set_user_database(database_manager)


@events.after_app_serving
async def shutdown_user_database() -> None:
    """
    Shutdown the server's user database
    """

    database_manager = await current_app.get_user_database()
    await database_manager.shutdown()


@p_events.before_app_serving
async def setup_race_database() -> None:
    """
    Sets the active race database for the server
    """
    database_manager = RaceDatabaseManager(filename="race.db")
    await database_manager.setup()
    current_app.set_race_database(database_manager)


@events.after_app_serving
async def shutdown_race_database() -> None:
    """
    Shutdown the server's race database
    """
    database_manager = await current_app.get_race_database()
    await database_manager.shutdown()


@events.after_app_serving
async def await_executor() -> None:
    """
    Shuts down the server's executor
    """
    await executor.shutdown_executor()
