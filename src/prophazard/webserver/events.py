"""
Webserver event handling
"""

import logging
from typing import Any

from quart import ResponseReturnValue, redirect, url_for
from quart_auth import Unauthorized

from tortoise import Tortoise, connections

from ..extensions import RHBlueprint, current_app
from ..events import SpecialEvt

from ..utils.executor import executor
from ..utils.config import configs

logger = logging.getLogger(__name__)

events = RHBlueprint("events", __name__)


@events.before_app_serving
async def log_startup() -> None:
    """
    Log the application startup
    """
    logger.info("Starting PropHazard...")


@events.after_app_serving
async def log_shutdown() -> None:
    """
    Log the application shutdown
    """
    logger.info("Stopping PropHazard...")


@events.while_app_serving
async def lifespan() -> Any:
    """
    Trigger startup and shutdown events
    """
    await Tortoise.generate_schemas(safe=True)

    logger.info("PropHazard startup completed...")
    current_app.event_broker.trigger(SpecialEvt.STARTUP, {})

    yield

    current_app.event_broker.trigger(SpecialEvt.SHUTDOWN, {})
    logger.info("PropHazard shutdown completed...")


@events.errorhandler(Unauthorized)
async def redirect_to_index(*_) -> ResponseReturnValue:
    """
    Redirects the user when `Unauthorized` to access
    a route or websocket

    :return: The server response
    """
    return redirect(url_for("index"))


@events.before_app_serving
async def database_startup() -> None:
    """
    Initialize the database
    """
    await Tortoise.init(
        {
            "connections": configs.get_config("DATABASE", "CONNECTIONS"),
            "apps": {
                "system": {
                    "models": ["prophazard.database"],
                    "default_connection": "system",
                },
                "event": {
                    "models": ["prophazard.database"],
                    "default_connection": "event",
                },
            },
        }
    )

    logger.debug("Tortoise-ORM started, %s", Tortoise.apps)

    await Tortoise.generate_schemas(safe=True)


@events.after_app_serving
async def database_shutdown() -> None:
    """
    Shutdown the database
    """
    await connections.close_all()

    logger.debug("Tortoise-ORM shutdown")


@events.before_app_serving
async def setup_global_executor() -> None:
    """
    Sets executor to uses for computationally intestive
    processing.
    """
    executor.set_executor()


@events.after_app_serving
async def await_executor() -> None:
    """
    Shuts down the server's executor
    """
    await executor.shutdown_executor()
