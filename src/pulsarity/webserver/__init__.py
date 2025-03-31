"""
Webserver Components
"""

from quart_auth import QuartAuth
from quart_schema import QuartSchema

from ..extensions import PulsarityApp, AppUser
from .events import events as _events
from .events import db_events as _db_events
from .routes import auth as _auth
from .routes import api as _api
from .websockets import websockets as _websockets

from ..utils.config import configs


def generate_app(*, test_mode: bool = False) -> PulsarityApp:
    """
    Generate a Pulsarity webserver application

    :param test_mode: Run in test mode. If set to True, the events blueprint
    will not be registered, defaults to False
    :return: _description_
    """

    app = PulsarityApp(__name__)

    app.secret_key = str(configs.get_config("SECRETS", "SECRET_KEY"))

    QuartAuth(
        app,
        cookie_domain=str(configs.get_config("WEBSERVER", "HOST")),
        cookie_name="PULSARITY_AUTH",
        cookie_samesite="Strict",
        mode="cookie",
        duration=86400,
        user_class=AppUser,
    )

    generate_api_docs = bool(configs.get_config("WEBSERVER", "API_DOCS"))
    QuartSchema(
        app,
        openapi_path="/api/openapi.json" if generate_api_docs else None,
        redoc_ui_path="/api/redocs" if generate_api_docs else None,
        scalar_ui_path="/api/scalar" if generate_api_docs else None,
        swagger_ui_path="/api/docs" if generate_api_docs else None,
    )

    for blueprint in (_events, _auth, _api, _websockets):
        app.register_blueprint(blueprint)

    if not test_mode:
        app.register_blueprint(_db_events)

    return app
