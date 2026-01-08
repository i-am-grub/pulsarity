"""
Webserver Components
"""

import asyncio
import contextlib
import json
import logging
from asyncio import Event
from collections.abc import Callable, Coroutine
from importlib.resources import files
from pathlib import Path
from typing import TypedDict

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware
from tortoise import Tortoise, connections

from pulsarity import ctx
from pulsarity.database import setup_default_objects
from pulsarity.events import EventBroker, SpecialEvt
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.processor import RaceProcessorManager
from pulsarity.race.state import RaceStateManager
from pulsarity.utils import background
from pulsarity.utils.crypto import generate_self_signed_cert
from pulsarity.webserver._auth import PulsarityAuthBackend
from pulsarity.webserver._wrapper import endpoint
from pulsarity.webserver.routes import ROUTES as http_routes
from pulsarity.webserver.websockets import ROUTES as ws_routes

logger = logging.getLogger(__name__)


class ContextState(TypedDict):
    """
    Context payload
    """

    loop: asyncio.AbstractEventLoop
    event: EventBroker
    race_state: RaceStateManager
    race_processor: RaceProcessorManager
    timer_inferface_manager: TimerInterfaceManager


class ContextMiddleware:
    """
    Middleware for propagating context into the application
    """

    # pylint: disable=R0903

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        state: ContextState = scope["state"]
        loop_token = ctx.loop_ctx.set(state["loop"])
        event_token = ctx.event_broker_ctx.set(state["event"])
        race_state_token = ctx.race_state_ctx.set(state["race_state"])
        race_processor_token = ctx.race_processor_ctx.set(state["race_processor"])
        timer_interface_token = ctx.interface_manager_ctx.set(
            state["timer_inferface_manager"]
        )

        try:
            await self.app(scope, receive, send)

        finally:
            ctx.loop_ctx.reset(loop_token)
            ctx.event_broker_ctx.reset(event_token)
            ctx.race_state_ctx.reset(race_state_token)
            ctx.race_processor_ctx.reset(race_processor_token)
            ctx.interface_manager_ctx.reset(timer_interface_token)


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


def _generate_static_files_application(path: str) -> SPAStaticFiles:
    """
    Generates the file serving application for SPAs.

    :return: The file serving application
    """
    return SPAStaticFiles(
        directory=Path(files("pulsarity.frontend.src") / path),  # type: ignore
        html=True,
    )


def generate_api_application() -> Starlette:
    """
    Generates the api and timing application with session and
    context middleware.

    :return: The api application object
    """
    configs = ctx.config_ctx.get()
    assert configs.secrets is not None

    middleware = [
        Middleware(
            SessionMiddleware,
            store=CookieStore(secret_key=configs.secrets.secret_key),
            cookie_https_only=configs.webserver.force_redirects,
            rolling=True,
            lifetime=60 * 30,
            cookie_same_site="strict",
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(AuthenticationMiddleware, backend=PulsarityAuthBackend()),
    ]

    return Starlette(
        routes=http_routes + ws_routes,  # type: ignore
        middleware=middleware,
    )


def generate_webserver_application() -> Starlette:
    """
    Generates the RotorHazard application with CORS middlesware and
    routes to the sub application.

    File serving app is mounted to the root of the domain (`/`) and the
    api application is mounted to (`/api`)

    :return: The webserver application
    """

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        Middleware(ContextMiddleware),
    ]

    routes = [
        Mount(path="/api", app=generate_api_application(), name="api"),
        Mount(
            path="/",
            app=_generate_static_files_application("client"),
            name="root",
        ),
    ]

    return Starlette(
        routes=routes,
        lifespan=lifespan,
        middleware=middleware,
    )


def generate_setup_application(shudown_evt: Event) -> Starlette:
    """
    Generates the "first time setup" application with CORS middlesware

    File serving app is mounted to the root of the domain (`/`) and the
    api application is mounted to (`/api`)

    :return: The webserver application
    """
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
    ]

    @endpoint(requires_auth=False)
    async def save_settings():
        """
        Validate setting data and save to config file
        """
        config = ctx.config_ctx.get()
        await config.write_config_to_file_async()
        shudown_evt.set()

    api_routes = [Route("/save", endpoint=save_settings, methods=["POST"])]
    routes = [
        Mount(path="/api", routes=api_routes, name="api"),
        Mount(
            path="/",
            app=_generate_static_files_application("startup"),
            name="root",
        ),
    ]

    return Starlette(routes=routes, middleware=middleware)


def generate_webserver_coroutine(
    app: Starlette, shutdown_trigger: Callable | None = None
) -> Coroutine[None, None, None]:
    """
    An awaitable task for the application deployed with a hypercorn ASGI server.

    This task is configured by reading parameters from the pulsarity config file

    :param app: Application to use for the webserver, defaults to None
    :return: Webserver coroutine
    """
    configs = ctx.config_ctx.get()
    assert configs.secrets is not None
    webserver_config = Config()

    host = configs.webserver.host

    port = configs.webserver.http_port
    webserver_config.insecure_bind = [f"{host}:{port}"]

    s_port = configs.webserver.https_port
    secure_bind = [f"{host}:{s_port}"]
    webserver_config.bind = secure_bind

    key_file = configs.webserver.key_file
    cert_file = configs.webserver.cert_file

    if not (key_file.is_file() and cert_file.is_file()):
        generate_self_signed_cert(key_file, cert_file)

    webserver_config.keyfile = str(key_file)
    webserver_config.certfile = str(cert_file)

    ca_cert_file = configs.webserver.ca_cert_file
    webserver_config.ca_certs = None if ca_cert_file is None else str(ca_cert_file)

    webserver_config.keyfile_password = configs.webserver.key_password

    if configs.webserver.force_redirects:
        app = HTTPToHTTPSRedirectMiddleware(app, secure_bind[0])  # type: ignore

    return serve(app, webserver_config, shutdown_trigger=shutdown_trigger)  # type: ignore


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
        race_state=RaceStateManager(),
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
    loop = state["loop"]
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
