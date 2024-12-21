"""
A demonstrator project for an asynchronous RotorHazard framework
"""

import os
import importlib.metadata
from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config

from .extensions import RHApplication
from .webserver import generate_app
from .config import get_config
from .utils.crypto import generate_self_signed_cert

__version__ = importlib.metadata.version(__name__)


def prophazard_webserver(
    app: RHApplication | None = None,
) -> Coroutine[None, None, None]:
    """
    An awaitable task for the application deployed with a hypercorn ASGI server.

    This task is configured by reading parameters from the prophazard config file

    :param RHApplication | None app: Application to use for the webserver, defaults to None
    :return Coroutine[None, None, None]: Webserver coroutine
    """

    webserver_config = Config()

    host = str(get_config("WEBSERVER", "HOST"))

    _port = get_config("WEBSERVER", "PORT")
    port = _port if isinstance(_port, int) else 5000

    webserver_config.bind = [f"{host}:{port}"]

    if bool(get_config("WEBSERVER", "USE_HTTPS")):

        key_file = str(get_config("WEBSERVER", "KEY_FILE"))
        cert_file = str(get_config("WEBSERVER", "CERT_FILE"))

        if not (os.path.isfile(key_file) and os.path.isfile(cert_file)):
            generate_self_signed_cert(key_file, cert_file)

        webserver_config.keyfile = key_file
        webserver_config.certfile = cert_file

        ca_cert_file = get_config("WEBSERVER", "CA_CERT_FILE")
        webserver_config.ca_certs = (
            ca_cert_file if isinstance(ca_cert_file, str) else None
        )

        key_file_password = get_config("WEBSERVER", "KEY_PASSWORD")
        webserver_config.keyfile_password = (
            key_file_password if isinstance(key_file_password, str) else None
        )

    webserver_config.debug = bool(get_config("GENERAL", "DEBUG"))

    if app is None:
        app = generate_app()

    return serve(app, webserver_config)
