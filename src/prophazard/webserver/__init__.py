

from .components import RHApplication, RHBlueprint
from .events import events as _events
from .routes import routes as _routes
from .tasks import tasks as _tasks
from .websockets import websockets as _websockets


def generate_app() -> RHApplication:

    app = RHApplication(__name__)

    app.secret_key = "secret key"

    for blueprint in (_events, _routes, _tasks, _websockets):
        app.register_blueprint(blueprint)

    return app
