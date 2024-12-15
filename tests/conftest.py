import asyncio
import pytest_asyncio

from prophazard.webserver import generate_app
from prophazard.database.race import RaceDatabaseManager
from prophazard.database.user import UserDatabaseManager
from prophazard.extensions import current_app, RHApplication


@pytest_asyncio.fixture()
async def race_database():
    race_database: RaceDatabaseManager = RaceDatabaseManager()
    await race_database.sync_database()
    yield race_database
    await race_database.shutdown()


@pytest_asyncio.fixture()
async def user_database():
    user_database: RaceDatabaseManager = UserDatabaseManager()
    await user_database.sync_database()
    yield user_database
    await user_database.shutdown()


@pytest_asyncio.fixture()
async def app():
    app = generate_app(test_mode=True)

    loop = asyncio.get_event_loop()
    app._user_database: asyncio.Future[UserDatabaseManager] = loop.create_future()
    app._race_database: asyncio.Future[RaceDatabaseManager] = loop.create_future()

    database_manager = UserDatabaseManager()
    await database_manager.sync_database()

    await database_manager.permissions.verify_persistant()
    permissions = await database_manager.permissions.get_all(None)
    await database_manager.roles.verify_persistant_role(
        None, "SYSTEM_ADMIN", set(permissions)
    )
    roles = set()
    roles.add(await database_manager.roles.role_by_name(None, "SYSTEM_ADMIN"))
    await database_manager.users.verify_persistant_user(None, "admin", roles)

    app.set_user_database(database_manager)

    database_manager = RaceDatabaseManager()
    await database_manager.sync_database()
    app.set_race_database(database_manager)

    yield app


@pytest_asyncio.fixture()
async def client(app: RHApplication):
    return app.test_client()
