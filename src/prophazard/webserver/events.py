from quart import redirect, url_for
from quart_auth import Unauthorized

from ..auth._authorizer import InvalidPermissions

from ..extensions import RHBlueprint, current_app

from ..database.user import UserDatabaseManager
from ..database.race import RaceDatabaseManager

from ..utils.executor import set_executor, shutdown_executor
from ..config import get_config_async

p_events = RHBlueprint("private_events", __name__)
events = RHBlueprint("events", __name__)


@events.errorhandler(Unauthorized)
async def redirect_to_index(*_):
    return redirect(url_for("index"))


@events.errorhandler(InvalidPermissions)
async def invalid_permissions(*_): ...


@events.before_app_serving
async def setup_global_executor():
    set_executor()


@p_events.before_app_serving
async def setup_user_database():
    database_manager = UserDatabaseManager(filename="user.db")
    await database_manager.setup()

    default_username = await get_config_async("SECRETS", "DEFAULT_USERNAME")
    default_password = await get_config_async("SECRETS", "DEFAULT_PASSWORD")

    await database_manager.verify_persistant_objects(default_username, default_password)

    current_app.set_user_database(database_manager)


@events.after_app_serving
async def shutdown_user_database():
    database_manager = await current_app.get_user_database()
    await database_manager.shutdown()


@p_events.before_app_serving
async def setup_race_database():
    database_manager = RaceDatabaseManager(filename="race.db")
    await database_manager.setup()
    current_app.set_race_database(database_manager)


@events.after_app_serving
async def shutdown_race_database():
    database_manager = await current_app.get_race_database()
    await database_manager.shutdown()


@events.after_app_serving
async def await_executor():
    await shutdown_executor()
