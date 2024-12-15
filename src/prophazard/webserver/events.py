from quart import redirect, url_for
from quart_auth import Unauthorized

from ..auth._authorizer import InvalidPermissions

from ..extensions import RHBlueprint, current_app

from ..database.user import UserDatabaseManager
from ..database.race import RaceDatabaseManager

p_events = RHBlueprint("private_events", __name__)
events = RHBlueprint("events", __name__)


@events.errorhandler(Unauthorized)
async def redirect_to_index(*_):
    return redirect(url_for("index"))


@events.errorhandler(InvalidPermissions)
async def invalid_permissions(*_): ...


@p_events.before_app_serving
async def setup_user_database():
    database_manager = UserDatabaseManager(filename="user.db")
    await database_manager.sync_database()

    await database_manager.permissions.verify_persistant()
    permissions = await database_manager.permissions.get_all(None)
    await database_manager.roles.verify_persistant_role(
        None, "SYSTEM_ADMIN", set(permissions)
    )
    roles = set()
    roles.add(await database_manager.roles.role_by_name(None, "SYSTEM_ADMIN"))
    await database_manager.users.verify_persistant_user(None, "admin", roles)

    current_app.set_user_database(database_manager)


@events.after_app_serving
async def shutdown_user_database():
    database_manager = await current_app.get_user_database()
    await database_manager.shutdown()


@p_events.before_app_serving
async def setup_race_database():
    database_manager = RaceDatabaseManager(filename="race.db")
    await database_manager.sync_database()
    current_app.set_race_database(database_manager)


@events.after_app_serving
async def shutdown_race_database():
    database_manager = await current_app.get_race_database()
    await database_manager.shutdown()
