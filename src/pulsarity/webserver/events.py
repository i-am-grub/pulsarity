"""
Webserver event handling
"""

import logging
import json
from typing import Any

from quart import ResponseReturnValue, redirect, url_for
from quart_auth import Unauthorized

from tortoise import Tortoise, connections

from ..extensions import PulsarityBlueprint, current_app
from ..events import SpecialEvt
from ..database import setup_default_objects

from ..utils.executor import executor
from ..utils.config import configs

logger = logging.getLogger(__name__)

events = PulsarityBlueprint("events", __name__)
db_events = PulsarityBlueprint("db_events", __name__)


@events.before_app_serving
async def server_startup() -> None:
    """
    Log the application startup
    """
    logger.info("Starting Pulsarity...")
    executor.set_executor()


@events.after_app_serving
async def server_shutdown() -> None:
    """
    Log the application shutdown
    """
    logger.info("Stopping Pulsarity...")
    await executor.shutdown_executor()


@events.while_app_serving
async def lifespan() -> Any:
    """
    Trigger startup and shutdown events
    """

    logger.info("Pulsarity startup completed...")
    current_app.event_broker.trigger(SpecialEvt.STARTUP, {})

    yield

    current_app.event_broker.trigger(SpecialEvt.SHUTDOWN, {})
    logger.info("Pulsarity shutdown completed...")


@db_events.before_app_serving
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


@db_events.after_app_serving
async def database_shutdown() -> None:
    """
    Shutdown the database
    """
    await connections.close_all()

    logger.debug("Database shutdown")


@events.errorhandler(Unauthorized)
async def redirect_to_index(*_) -> ResponseReturnValue:
    """
    Redirects the user when `Unauthorized` to access
    a route or websocket

    :return: The server response
    """
    return redirect(url_for("index"))
