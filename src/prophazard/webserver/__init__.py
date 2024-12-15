"""
Webserver Components
"""

from quart_auth import QuartAuth
from secrets import token_urlsafe

from ..extensions import RHApplication, RHBlueprint, RHUser
from .events import p_events as _p_events
from .events import events as _events
from .routes import routes as _routes
from .tasks import tasks as _tasks
from .websockets import websockets as _websockets

from ..config import get_item_from_file


def generate_app(*, test_mode: bool = False) -> RHApplication:
    """
    Generate a PropHazard webserver application

    :param bool test_mode: Run in test mode. If set to True, the events blueprint
    will not be registered, defaults to False
    :return RHApplication: _description_
    """

    app = RHApplication(__name__)

    app.secret_key = str(get_item_from_file("SECRETS", "SECRET_KEY"))

    QuartAuth(
        app,
        cookie_name="PROPHAZARD_AUTH",
        mode="cookie",
        user_class=RHUser,
    )

    for blueprint in (_events, _routes, _tasks, _websockets):
        app.register_blueprint(blueprint)

    if not test_mode:
        app.register_blueprint(_p_events)

    return app
