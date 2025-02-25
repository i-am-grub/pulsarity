import os

import pytest
import pytest_asyncio
from tortoise.contrib.test import finalizer, initializer, init_memory_sqlite

from prophazard.webserver import generate_app
from prophazard.extensions import RHApplication

from prophazard.database.raceformat import RaceFormat, RaceSchedule


@pytest_asyncio.fixture()
async def default_user_creds():
    username = "admin"
    password = "test_password"

    return username, password


@pytest_asyncio.fixture(scope="function")
async def app():
    yield generate_app(test_mode=True)


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request: pytest.FixtureRequest):
    initializer(["app.database"])
    request.addfinalizer(finalizer)


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
