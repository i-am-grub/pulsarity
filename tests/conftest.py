import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from tortoise import Tortoise, connections

from pulsarity.database import setup_default_objects
from pulsarity.database.raceformat import RaceSchedule
from pulsarity.utils.background import background_tasks
from pulsarity.utils.config import get_configs_defaults
from pulsarity.webserver import generate_application


@pytest_asyncio.fixture(name="database", scope="function")
async def database_init():

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
                    "models": ["pulsarity.database"],
                    "default_connection": "system",
                },
                "event": {
                    "models": ["pulsarity.database"],
                    "default_connection": "event",
                },
            },
        }
    )
    await Tortoise.generate_schemas()

    await setup_default_objects()

    yield

    await connections.close_all()


@pytest_asyncio.fixture(name="app", scope="function")
async def application(database):

    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    yield generate_application(test_mode=True)

    await background_tasks.shutdown(5)


@pytest_asyncio.fixture(name="client", scope="function")
async def unauthenticated_client(app: Starlette):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="https://localhost", verify=False, timeout=5
    ) as client_:
        yield client_


@pytest.fixture(name="user_creds")
def default_user_creds():

    configs = get_configs_defaults()

    username = str(configs["SECRETS"]["DEFAULT_USERNAME"])
    password = str(configs["SECRETS"]["DEFAULT_PASSWORD"])

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
