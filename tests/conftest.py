import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise, connections

from pulsarity import ctx
from pulsarity.database import setup_default_objects
from pulsarity.utils import background
from pulsarity.utils.config import get_configs_defaults
from pulsarity.webserver import generate_application


@pytest_asyncio.fixture(autouse=True)
async def context_and_cleanup():
    loop = asyncio.get_running_loop()
    ctx.loop_ctx.set(loop)

    yield

    background.shutdown(5)


@pytest_asyncio.fixture(autouse=True)
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


@pytest_asyncio.fixture(name="client")
async def unauthenticated_client():
    transport = ASGITransport(app=generate_application(test_mode=True))
    async with AsyncClient(
        transport=transport, base_url="https://localhost", verify=False, timeout=5
    ) as client_:
        yield client_


@pytest.fixture(name="user_creds")
def default_user_creds():
    configs = get_configs_defaults()

    username = str(configs["SECRETS"]["DEFAULT_USERNAME"])
    password = str(configs["SECRETS"]["DEFAULT_PASSWORD"])

    yield username, password
