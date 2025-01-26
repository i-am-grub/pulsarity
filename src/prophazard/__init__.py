"""
A demonstrator project for an asynchronous RotorHazard framework
"""

import os
import importlib.metadata
from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware

from .extensions import RHApplication
from .webserver import generate_app
from .config import configs
from .utils.crypto import generate_self_signed_cert

__version__ = importlib.metadata.version(__name__)


def prophazard_webserver(
    app: RHApplication | None = None,
) -> Coroutine[None, None, None]:
    """
    An awaitable task for the application deployed with a hypercorn ASGI server.

    This task is configured by reading parameters from the prophazard config file

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

    webserver_config.debug = bool(configs.get_config("GENERAL", "DEBUG"))

    if app is None:
        app = generate_app()

    redirects = configs.get_config("WEBSERVER", "FORCE_REDIRECTS")
    if redirects:
        app = HTTPToHTTPSRedirectMiddleware(app, secure_bind[0])  # type: ignore

    return serve(app, webserver_config)
