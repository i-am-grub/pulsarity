"""
A demonstrator project for an asynchronous RotorHazard framework
"""

from collections.abc import Coroutine

from hypercorn.asyncio import serve
from hypercorn.config import Config

from quart.typing import TestAppProtocol, TestClientProtocol

from .webserver.components import RHApplication
from .webserver import generate_app
from .config import get_item_from_file

def test_app(app: RHApplication | None = None) -> TestAppProtocol:
    """
    Generates a test app to be used for teseting the webserver

    :param RHApplication | None app: Application to use for the webserver, defaults to None
    :return TestAppProtocol: The generated test application
    """

    if app is None:
        app = generate_app()

    return app.test_app()


def test_client(app: RHApplication | None = None) -> TestClientProtocol:
    """
    Generates a client to be used for testing the webserver

    :param RHApplication | None app: Application to use for the webserver, defaults to None
    :return TestClientProtocol: The generated test client
    """

    if app is None:
        app = generate_app()

    return app.test_client()

def prophazard_webserver(app: RHApplication | None = None) -> Coroutine[None, None, None]:
    """
    An awaitable task for the application with a hypercorn production ASGI server. 
    
    This task is configured by reading parameters from the prophazard config file

    :param RHApplication | None app: Application to use for the webserver, defaults to None
    :return _type_: _description_
    """

    webserver_config = Config()

    host = str(get_item_from_file("GENERAL", "HOST"))

    _port = get_item_from_file("GENERAL", "HTTP_PORT")
    port = _port if isinstance(_port, int) else 5000

    webserver_config.bind = f"{host}:{port}"
    webserver_config.debug = bool(get_item_from_file("GENERAL", "DEBUG"))

    if app is None:
        app = generate_app()

    return serve(app, webserver_config)