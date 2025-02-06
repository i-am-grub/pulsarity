import pytest_asyncio

from prophazard.webserver import generate_app
from prophazard.database.race import RaceDatabaseManager
from prophazard.database.user import UserDatabaseManager
from prophazard.extensions import RHApplication

from prophazard.database.race._orm.raceformat import RaceFormat, RaceSchedule


@pytest_asyncio.fixture()
async def default_user_creds():
    username = "admin"
    password = "test_password"

    return username, password


@pytest_asyncio.fixture(scope="function")
async def user_database(default_user_creds):
    user_database_: UserDatabaseManager = UserDatabaseManager()
    await user_database_.setup()
    await user_database_.verify_persistant_objects(*default_user_creds)
    yield user_database_
    await user_database_.shutdown()


@pytest_asyncio.fixture(scope="function")
async def race_database():
    race_database_: RaceDatabaseManager = RaceDatabaseManager()
    await race_database_.setup()
    yield race_database_
    await race_database_.shutdown()


@pytest_asyncio.fixture(scope="function")
async def app(user_database: UserDatabaseManager, race_database: RaceDatabaseManager):
    app_ = generate_app(test_mode=True)

    app_.set_user_database(user_database)
    app_.set_race_database(race_database)

    yield app_


@pytest_asyncio.fixture()
async def client(app: RHApplication):
    yield app.test_client()


@pytest_asyncio.fixture()
async def limited_schedule():
    yield RaceSchedule(3, 0, False, 5, 2)


@pytest_asyncio.fixture()
async def limited_no_ot_schedule():
    yield RaceSchedule(3, 0, False, 5, 0)


@pytest_asyncio.fixture()
async def unlimited_schedule():
    yield RaceSchedule(5, 1, True, 10, 5)
