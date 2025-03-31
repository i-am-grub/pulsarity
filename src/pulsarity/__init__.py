"""
A demonstrator project for an asynchronous RotorHazard framework
"""

from __future__ import annotations

import os
import signal
import asyncio
import logging
import importlib.metadata
from typing import Any
from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware

from .extensions import PulsarityApp
from .webserver import generate_app
from .utils.config import configs
from .utils.crypto import generate_self_signed_cert

__version__ = importlib.metadata.version(__name__)

_shutdown_event = asyncio.Event()
logger = logging.getLogger(__name__)


def _signal_shutdown(*_: Any) -> None:
    """
    Set the event to shutdown the server gracefully
    """
    _shutdown_event.set()
    logger.debug("Server shutdown signaled")


def _add_signal_callback(app: PulsarityApp) -> None:
    """
    Add a callback to system signal

    :param app: The application to use for referencing the event loop.
    A handler will be added to the targeted event loop.
    """

    @app.before_serving
    async def _register_shutdown_signals() -> None:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.Signals.SIGINT, _signal_shutdown)
        loop.add_signal_handler(signal.Signals.SIGTERM, _signal_shutdown)


def pulsarity_webserver(
    app: PulsarityApp | None = None,
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
        app = generate_app()

    _add_signal_callback(app)

    redirects = configs.get_config("WEBSERVER", "FORCE_REDIRECTS")
    if redirects:
        app = HTTPToHTTPSRedirectMiddleware(app, secure_bind[0])  # type: ignore

    return serve(app, webserver_config, shutdown_trigger=_shutdown_event.wait)
