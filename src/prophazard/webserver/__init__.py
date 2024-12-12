"""
Webserver Components
"""

from .components import RHApplication, RHBlueprint
from .routes import routes as _routes
from .tasks import tasks as _tasks
from .websockets import websockets as _websockets


def generate_app() -> RHApplication:
    """
    Generate a PropHazard webserver application

    :return RHApplication: _description_
    """

    app = RHApplication(__name__)

    app.secret_key = "secret key"

    for blueprint in (_routes, _tasks, _websockets):
        app.register_blueprint(blueprint)

    return app
