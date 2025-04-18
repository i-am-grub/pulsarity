"""
Webserver Components
"""

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from ..utils.config import configs
from .auth import AuthenticationBackend
from .events import lifespan as _lifespan
from .routes import routes as http_routes
from .websockets import routes as ws_routes


def generate_application() -> Starlette:
    """
    Generates the Pulsarity application

    :return: The starlette application object
    """

    middleware = [
        Middleware(
            SessionMiddleware,
            secret_key=str(configs.get_config("SECRETS", "SECRET_KEY")),
            domain=str(configs.get_config("WEBSERVER", "HOST")),
        ),
        Middleware(AuthenticationMiddleware, backend=AuthenticationBackend()),
    ]

    all_routes = http_routes + ws_routes

    return Starlette(routes=all_routes, lifespan=_lifespan, middleware=middleware)
