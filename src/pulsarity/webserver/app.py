"""
Webserver Components
"""

import logging
from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from pulsarity import ctx
from pulsarity.utils.crypto import generate_self_signed_cert
from pulsarity.webserver._auth import PulsarityAuthBackend
from pulsarity.webserver.lifespan import ContextState, shutdown_signaled
from pulsarity.webserver.lifespan import lifespan as _lifespan
from pulsarity.webserver.routes import ROUTES as http_routes
from pulsarity.webserver.websockets import ROUTES as ws_routes

logger = logging.getLogger(__name__)


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


def generate_application(*, test_mode: bool = False) -> Starlette:
    """
    Generates the Pulsarity application

    :return: The starlette application object
    """
    configs = ctx.config_ctx.get()
    assert configs.secrets is not None

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
        ),
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

    if not test_mode:
        middleware.append(Middleware(ContextMiddleware))

    routes = [
        Mount(path="/api", routes=http_routes + ws_routes, name="api"),  # type: ignore
    ]

    if configs.webserver.spa_path is not None:
        routes.append(
            Mount(
                path="/",
                app=SPAStaticFiles(
                    directory=configs.webserver.spa_path,
                    html=True,
                ),
                name="root",
            ),
        )

    return Starlette(
        routes=routes,
        lifespan=None if test_mode else _lifespan,
        middleware=middleware,
    )


def generate_webserver_coroutine(
    app: Starlette | None = None,
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

    if app is None:
        app = generate_application()

    if configs.webserver.force_redirects:
        app = HTTPToHTTPSRedirectMiddleware(app, secure_bind[0])  # type: ignore

    return serve(app, webserver_config, shutdown_trigger=shutdown_signaled)  # type: ignore
