"""
Webserver Components
"""

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from ..utils.config import configs
from .auth import PulsarityAuthBackend
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
            store=CookieStore(
                secret_key=str(configs.get_config("SECRETS", "SECRET_KEY"))
            ),
            cookie_https_only=bool(configs.get_config("SECRETS", "FORCE_REDIRECTS")),
            rolling=True,
            lifetime=30,
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(AuthenticationMiddleware, backend=PulsarityAuthBackend()),
    ]

    all_routes = http_routes + ws_routes

    return Starlette(routes=all_routes, lifespan=_lifespan, middleware=middleware)
