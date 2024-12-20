import pytest_asyncio

from prophazard.webserver import generate_app
from prophazard.database.race import RaceDatabaseManager
from prophazard.database.user import UserDatabaseManager
from prophazard.extensions import RHApplication


@pytest_asyncio.fixture()
async def default_user_creds():
    username = "admin"
    password = "test_password"

    return username, password


@pytest_asyncio.fixture()
async def user_database(default_user_creds):
    user_database: UserDatabaseManager = UserDatabaseManager()
    await user_database.setup()
    await user_database.verify_persistant_objects(*default_user_creds)
    yield user_database
    await user_database.shutdown()


@pytest_asyncio.fixture()
async def race_database():
    race_database: RaceDatabaseManager = RaceDatabaseManager()
    await race_database.setup()
    yield race_database
    await race_database.shutdown()


@pytest_asyncio.fixture()
async def app(user_database: UserDatabaseManager, race_database: RaceDatabaseManager):
    app = generate_app(test_mode=True)

    app.set_user_database(user_database)
    app.set_race_database(race_database)

    yield app


@pytest_asyncio.fixture()
async def client(app: RHApplication):
    return app.test_client()
