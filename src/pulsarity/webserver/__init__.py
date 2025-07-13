"""
Webserver Components
"""

import logging
import os
from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from pulsarity.utils.config import configs
from pulsarity.utils.crypto import generate_self_signed_cert
from pulsarity.webserver.auth import PulsarityAuthBackend
from pulsarity.webserver.events import lifespan as _lifespan
from pulsarity.webserver.events import shutdown_signaled
from pulsarity.webserver.routes import routes as http_routes
from pulsarity.webserver.websockets import routes as ws_routes

logger = logging.getLogger(__name__)


def generate_application(*, test_mode: bool = False) -> Starlette:
    """
    Generates the Pulsarity application

    :return: The starlette application object
    """

    middleware = [
        Middleware(
            SessionMiddleware,
            store=CookieStore(
                secret_key=str(configs.get_config("SECRETS", "SECRET_KEY"))
            ),
            cookie_https_only=bool(configs.get_config("WEBSERVER", "FORCE_REDIRECTS")),
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

    webserver_config = Config()

    host = str(configs.get_config("WEBSERVER", "HOST"))

    _port = configs.get_config("WEBSERVER", "HTTP_PORT")
    port = _port if isinstance(_port, int) else 5000
    webserver_config.insecure_bind = [f"{host}:{port}"]

    _s_port = configs.get_config("WEBSERVER", "HTTPS_PORT")
    s_port = _s_port if isinstance(_s_port, int) else 5443
    secure_bind = [f"{host}:{s_port}"]
    webserver_config.bind = secure_bind

    key_file = str(configs.get_config("WEBSERVER", "KEY_FILE"))
    cert_file = str(configs.get_config("WEBSERVER", "CERT_FILE"))

    if not (os.path.isfile(key_file) and os.path.isfile(cert_file)):
        generate_self_signed_cert(key_file, cert_file)

    webserver_config.keyfile = key_file
    webserver_config.certfile = cert_file

    ca_cert_file = configs.get_config("WEBSERVER", "CA_CERT_FILE")
    webserver_config.ca_certs = (
        ca_cert_file if isinstance(ca_cert_file, str) and ca_cert_file else None
    )

    key_file_pass = configs.get_config("WEBSERVER", "KEY_PASSWORD")
    webserver_config.keyfile_password = (
        key_file_pass if isinstance(key_file_pass, str) and key_file_pass else None
    )

    if app is None:
        app = generate_application()

    if bool(configs.get_config("WEBSERVER", "FORCE_REDIRECTS")):
        app = HTTPToHTTPSRedirectMiddleware(app, secure_bind[0])  # type: ignore

    return serve(app, webserver_config, shutdown_trigger=shutdown_signaled)  # type: ignore
