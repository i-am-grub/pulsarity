"""
Webserver Components
"""

import asyncio
import contextlib
import itertools
import logging
from importlib.resources import files
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware
from tortoise import Tortoise
from tortoise.contrib.starlette import register_tortoise

from pulsarity import _native
from pulsarity._core import ctx, database
from pulsarity._core.events.server import ServerShutdown, ServerStartup, SystemHeartBeat
from pulsarity._core.utils import background, config
from pulsarity._core.webserver import http, websockets
from pulsarity._core.webserver._auth import PulsarityAuthBackend

logger = logging.getLogger(__name__)


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
        routes=http.ROUTES + websockets.ROUTES,
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

    routes = [
        Mount(path="/api", app=generate_api_application(), name="api"),
    ]

    try:
        spa_app = SPAStaticFiles(
            directory=Path(files("pulsarity") / "frontend"),  # pyright: ignore[reportArgumentType]
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

    app = Starlette(
        routes=routes,
        lifespan=lifespan,
    )

    register_tortoise(
        app,
        config={
            "connections": config.config_manager.database.model_dump(),
            "apps": {
                "system": {
                    "models": ["pulsarity._core.database"],
                    "default_connection": "system_db",
                },
                "event": {
                    "models": ["pulsarity._core.database"],
                    "default_connection": "event_db",
                },
            },
            "use_tz": False,
            "timezone": "UTC",
        },
        generate_schemas=True,
    )

    return app


async def heartbeat_coroutine():
    """
    Publish a heartbeat event at 15 second intervals
    """
    evt = asyncio.Event()

    for i in itertools.count(start=ctx.evt_loop.time(), step=15.0):
        ctx.evt_loop.call_at(i, evt.set)
        await evt.wait()
        evt.clear()

        ctx.event_broker.publish(SystemHeartBeat())
        logger.debug("Server heartbeat...")


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    """
    Startup and shutdown procedures for the webserver. The states created
    during the startup phase of the lifespan can be propagated to the
    request via the `ContextState` dictionary.
    """

    logger.info("Starting application")

    await database.setup_default_objects()

    logger.debug("Using databases: %s", tuple(Tortoise.apps))
    logger.info("Database connections started")

    heartbeat_task = ctx.evt_loop.create_task(
        heartbeat_coroutine(),
        name="heartbeat_task",
    )

    await server_starup_workflow()

    logger.info("Application startup completed")

    yield

    logger.info("Stopping application")

    heartbeat_task.cancel()

    await server_shutdown_workflow()

    with contextlib.suppress(asyncio.CancelledError):
        await heartbeat_task

    logger.info("Database connections closed")

    logger.info("Application shutdown completed")


async def server_starup_workflow() -> None:
    """
    Startup workflow
    """
    _native.import_all_submodules()
    ctx.timer_manager.start()
    await ctx.event_broker.trigger(ServerStartup())


async def server_shutdown_workflow() -> None:
    """
    Shutdown workflow
    """
    await ctx.event_broker.trigger(ServerShutdown())
    await ctx.timer_manager.shutdown()
    websockets.ws_shutdown_evt.set()
    await background.shutdown(5)
