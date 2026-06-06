"""
Webserver Components
"""

import asyncio
import contextlib
import logging
from importlib.resources import files
from pathlib import Path
from typing import ClassVar, TypedDict

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware
from tortoise import Tortoise
from tortoise.context import TortoiseContext
from tortoise.context import _current_context as db_context

from pulsarity import ctx, defaults
from pulsarity.database import setup_default_objects
from pulsarity.events import EventBroker
from pulsarity.events.server import ServerShutdown, ServerStartup
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.manager import RaceManager
from pulsarity.utils import background, config
from pulsarity.webserver._auth import PulsarityAuthBackend
from pulsarity.webserver.http import ROUTES as HTTP_ROUTES
from pulsarity.webserver.websockets import ROUTES as WS_ROUTES

logger = logging.getLogger(__name__)


class ContextState(TypedDict):
    """
    Context payload
    """

    loop: asyncio.AbstractEventLoop
    event_broker: EventBroker
    race_manager: RaceManager
    timer_manager: TimerInterfaceManager
    database_ctx: TortoiseContext


class ContextMiddleware:
    """
    Middleware for propagating context into the application
    """

    __slots__ = ("app",)

    _context_request_types: ClassVar[set[str]] = {"http", "websocket"}

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in self._context_request_types:
            return await self.app(scope, receive, send)

        state: ContextState = scope["state"]
        loop_token = ctx.loop_ctx.set(state["loop"])
        event_token = ctx.event_broker_ctx.set(state["event_broker"])
        race_manager_token = ctx.race_manager_ctx.set(state["race_manager"])
        timer_manager_token = ctx.timer_manager_ctx.set(state["timer_manager"])
        db_context_token = db_context.set(state["database_ctx"])

        try:
            await self.app(scope, receive, send)

        finally:
            ctx.loop_ctx.reset(loop_token)
            ctx.event_broker_ctx.reset(event_token)
            ctx.race_manager_ctx.reset(race_manager_token)
            ctx.timer_manager_ctx.reset(timer_manager_token)
            db_context.reset(db_context_token)


class SPAStaticFiles(StaticFiles):
    """
    Staticfiles for single-page-apps

    Wraps the base `lookup_path` to fallback to the root `index.html`.
    """

    def lookup_path(self, path):
        full_path, stat_result = super().lookup_path(path)
        if stat_result is None:
            return super().lookup_path("./index.html")

        return full_path, stat_result


def generate_api_application() -> Starlette:
    """
    Generates the api and timing application with session and
    context middleware.

    :return: The api application object
    """
    configs = config.config_manager

    middleware = [
        Middleware(
            SessionMiddleware,
            store=CookieStore(secret_key=configs.secrets.secret_key),
            cookie_https_only=configs.webserver.using_ssl,
            rolling=True,
            lifetime=60 * 30,
            cookie_same_site="strict",
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(AuthenticationMiddleware, backend=PulsarityAuthBackend()),
    ]

    return Starlette(
        routes=HTTP_ROUTES + WS_ROUTES,  # type: ignore
        middleware=middleware,
    )


def generate_pulsarity_application() -> Starlette:
    """
    Generates the Pulsarity application with CORS middlesware and
    routes to the sub application.

    File serving app is mounted to the root of the domain (`/`) and the
    api application is mounted to (`/api`)

    :return: The webserver application
    """

    middleware = [
        Middleware(ContextMiddleware),
    ]

    routes = [
        Mount(path="/api", app=generate_api_application(), name="api"),
    ]

    try:
        spa_app = SPAStaticFiles(
            directory=Path(files("pulsarity") / "frontend"),  # type: ignore
            html=True,
        )

    except RuntimeError:
        msg = (
            "Servable front-end files were not found at pulsartiy.frontend."
            "The application will run headless."
        )
        logger.warning(msg)

    else:
        routes.append(Mount(path="/", app=spa_app, name="root"))

    return Starlette(
        routes=routes,
        lifespan=lifespan,
        middleware=middleware,
    )


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    """
    Startup and shutdown procedures for the webserver. The states created
    during the startup phase of the lifespan can be propagated to the
    request via the `ContextState` dictionary.
    """

    logger.info("Starting application")

    async with TortoiseContext() as db_ctx:
        await db_ctx.init(
            {
                "connections": config.config_manager.database.model_dump(),
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
                "use_tz": False,
                "timezone": "UTC",
            }
        )
        await db_ctx.generate_schemas(True)

        await setup_default_objects()

        logger.debug("Using databases: %s", tuple(Tortoise.apps))
        logger.info("Database connections started")

        state = ContextState(
            loop=asyncio.get_running_loop(),
            event_broker=EventBroker(),
            race_manager=RaceManager(),
            timer_manager=TimerInterfaceManager(),
            database_ctx=db_ctx,
        )

        loop_token = ctx.loop_ctx.set(state["loop"])
        event_token = ctx.event_broker_ctx.set(state["event_broker"])
        race_manager_token = ctx.race_manager_ctx.set(state["race_manager"])
        timer_manager_token = ctx.timer_manager_ctx.set(state["timer_manager"])

        await server_starup_workflow()

        logger.info("Application startup completed")

        yield state

        logger.info("Stopping application")

        await server_shutdown_workflow()

    logger.info("Database connections closed")

    ctx.loop_ctx.reset(loop_token)
    ctx.event_broker_ctx.reset(event_token)
    ctx.race_manager_ctx.reset(race_manager_token)
    ctx.timer_manager_ctx.reset(timer_manager_token)

    logger.info("Application shutdown completed")


async def server_starup_workflow() -> None:
    """
    Startup workflow
    """
    defaults.import_all_submodules()
    ctx.timer_manager_ctx.get().start()

    await ctx.event_broker_ctx.get().trigger(ServerStartup())


async def server_shutdown_workflow() -> None:
    """
    Shutdown workflow
    """
    await ctx.event_broker_ctx.get().trigger(ServerShutdown())
    await ctx.timer_manager_ctx.get().shutdown(5)
    await background.shutdown(5)
