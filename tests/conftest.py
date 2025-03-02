import pytest
import pytest_asyncio

from tortoise import Tortoise, connections

from prophazard.webserver import generate_app
from prophazard.extensions import RHApplication
from prophazard.database import setup_default_objects

from prophazard.database.raceformat import RaceSchedule

from prophazard.utils.config import get_configs_defaults


@pytest.fixture()
def app():
    yield generate_app(test_mode=True)


@pytest.fixture()
def client(app: RHApplication):
    yield app.test_client()


@pytest_asyncio.fixture(name="_setup_database")
async def setup_database():

    await Tortoise.init(
        {
            "connections": {
                "system": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": ":memory:"},
                },
                "event": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": ":memory:"},
                },
            },
            "apps": {
                "system": {
                    "models": ["prophazard.database"],
                    "default_connection": "system",
                },
                "event": {
                    "models": ["prophazard.database"],
                    "default_connection": "event",
                },
            },
        }
    )
    await Tortoise.generate_schemas()

    await setup_default_objects()

    yield

    await connections.close_all()


@pytest.fixture()
def default_user_creds():

    configs = get_configs_defaults()

    username = configs["SECRETS"]["DEFAULT_USERNAME"]
    password = configs["SECRETS"]["DEFAULT_PASSWORD"]

    return username, password


@pytest.fixture()
def limited_schedule():
    yield RaceSchedule(3, 0, False, 5, 2)


@pytest.fixture()
def limited_no_ot_schedule():
    yield RaceSchedule(3, 0, False, 5, 0)


@pytest.fixture()
def unlimited_schedule():
    yield RaceSchedule(5, 1, True, 10, 5)
