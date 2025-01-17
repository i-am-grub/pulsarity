"""
Webserver Components
"""

from quart_auth import QuartAuth
from quart_schema import QuartSchema

from ..extensions import RHApplication, RHUser
from .events import p_events as _p_events
from .events import events as _events
from .routes import files as _files
from .routes import auth as _auth
from .routes import api as _api
from .tasks import tasks as _tasks
from .websockets import websockets as _websockets

from ..config import get_config


def generate_app(*, test_mode: bool = False) -> RHApplication:
    """
    Generate a PropHazard webserver application

    :param bool test_mode: Run in test mode. If set to True, the events blueprint
    will not be registered, defaults to False
    :return RHApplication: _description_
    """

    app = RHApplication(__name__)

    app.secret_key = str(get_config("SECRETS", "SECRET_KEY"))

    QuartAuth(
        app,
        cookie_domain=str(get_config("WEBSERVER", "HOST")),
        cookie_name="PROPHAZARD_AUTH",
        cookie_samesite="Strict",
        mode="cookie",
        duration=86400,
        user_class=RHUser,
    )

    generate_api_docs = bool(get_config("GENERAL", "DEBUG"))
    QuartSchema(
        app,
        openapi_path="/api/openapi.json" if generate_api_docs else None,
        redoc_ui_path="/api/redocs" if generate_api_docs else None,
        scalar_ui_path="/api/scalar" if generate_api_docs else None,
        swagger_ui_path="/api/docs" if generate_api_docs else None,
    )

    for blueprint in (_events, _files, _auth, _api, _tasks, _websockets):
        app.register_blueprint(blueprint)

    if not test_mode:
        app.register_blueprint(_p_events)

    return app
