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
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from pulsarity import ctx
from pulsarity.utils.crypto import generate_self_signed_cert
from pulsarity.webserver.auth import PulsarityAuthBackend
from pulsarity.webserver.lifespan import lifespan as _lifespan
from pulsarity.webserver.lifespan import shutdown_signaled
from pulsarity.webserver.routes import routes as http_routes
from pulsarity.webserver.websockets import routes as ws_routes

logger = logging.getLogger(__name__)


def generate_application(*, test_mode: bool = False) -> Starlette:
    """
    Generates the Pulsarity application

    :return: The starlette application object
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
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(AuthenticationMiddleware, backend=PulsarityAuthBackend()),
    ]

    all_routes = http_routes + ws_routes

    return Starlette(
        routes=all_routes,
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
