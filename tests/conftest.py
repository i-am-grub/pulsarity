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
    user_database: UserDatabaseManager = UserDatabaseManager()
    await user_database.setup()
    await user_database.verify_persistant_objects(*default_user_creds)
    yield user_database
    await user_database.shutdown()


@pytest_asyncio.fixture(scope="function")
async def race_database():
    race_database: RaceDatabaseManager = RaceDatabaseManager()
    await race_database.setup()
    yield race_database
    await race_database.shutdown()


@pytest_asyncio.fixture(scope="function")
async def app(user_database: UserDatabaseManager, race_database: RaceDatabaseManager):
    app = generate_app(test_mode=True)

    app.set_user_database(user_database)
    app.set_race_database(race_database)

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(app: RHApplication):
    yield app.test_client()


@pytest_asyncio.fixture()
async def limited_format():
    schedule = RaceSchedule(3, 0, False, 5, 2)
    format_ = RaceFormat(schedule)
    yield format_


@pytest_asyncio.fixture()
async def limited_no_ot_format():
    schedule = RaceSchedule(3, 0, False, 5, 0)
    format_ = RaceFormat(schedule)
    yield format_


@pytest_asyncio.fixture()
async def unlimited_format():
    schedule = RaceSchedule(5, 1, True, 10, 5)
    format_ = RaceFormat(schedule)
    yield format_
