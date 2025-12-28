"""
Pytest default fixtures
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise, connections

from pulsarity import ctx
from pulsarity.database import (
    Heat,
    Pilot,
    RaceClass,
    RaceEvent,
    RaceFormat,
    Round,
    Slot,
    setup_default_objects,
)
from pulsarity.events.broker import EventBroker
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.processor import RaceProcessorManager
from pulsarity.race.state import RaceStateManager
from pulsarity.utils import background
from pulsarity.utils.config import PulsarityConfig
from pulsarity.webserver import generate_application


@pytest_asyncio.fixture(autouse=True)
async def context_and_cleanup():
    """
    Setup and tear down the application context
    """

    ctx.loop_ctx.set(asyncio.get_running_loop())
    ctx.event_broker_ctx.set(EventBroker())
    ctx.race_state_ctx.set(RaceStateManager())
    ctx.race_processor_ctx.set(RaceProcessorManager())
    ctx.interface_manager_ctx.set(TimerInterfaceManager())

    yield

    await background.shutdown(5)


@pytest_asyncio.fixture(autouse=True)
async def database_init():
    """
    Establish the test database connection
    """

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
    """
    Generate an unauthenticated client
    """

    transport = ASGITransport(app=generate_application(test_mode=True))
    async with AsyncClient(
        transport=transport, base_url="https://localhost/api"
    ) as client_:
        yield client_


@pytest.fixture(name="user_creds")
def default_user_creds():
    """
    Generates default authentication creds
    """
    configs = PulsarityConfig()

    username = configs.secrets.default_username
    password = configs.secrets.default_password

    yield username, password


@pytest_asyncio.fixture(name="authed_client")
async def _authenticated_client(client: AsyncClient, user_creds: tuple[str, str]):
    """
    Generates an authenticated client
    """
    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    yield client


@pytest_asyncio.fixture(name="limited_schedule")
async def _limited_schedule():
    return await RaceFormat.create(
        name="limited_schedule",
        stage_time_sec=1,
        random_stage_delay=0,
        unlimited_time=False,
        race_time_sec=2,
        overtime_sec=1,
        processor_id="foo-bar",
    )


@pytest_asyncio.fixture(name="limited_no_ot_schedule")
async def _limited_no_ot_schedule():
    return await RaceFormat.create(
        name="limited_no_ot_schedule",
        stage_time_sec=1,
        random_stage_delay=0,
        unlimited_time=False,
        race_time_sec=2,
        overtime_sec=0,
        processor_id="foo-bar",
    )


@pytest_asyncio.fixture(name="unlimited_schedule")
async def _unlimited_schedule():
    return await RaceFormat.create(
        name="unlimited_schedule",
        stage_time_sec=1,
        random_stage_delay=0,
        unlimited_time=True,
        race_time_sec=2,
        overtime_sec=1,
        processor_id="foo-bar",
    )


@pytest_asyncio.fixture(name="basic_event")
async def _basic_event():
    return await RaceEvent.create(name_="Test Event")


@pytest_asyncio.fixture(name="basic_raceclass")
async def _basic_raceclass(basic_event: RaceEvent, limited_schedule: RaceFormat):
    async with RaceClass.lock:
        value = await basic_event.get_next_raceclass_num()
        return await RaceClass.create(
            name_="Test RaceClass",
            event=basic_event,
            raceclass_num=value,
            raceformat=limited_schedule,
        )


@pytest_asyncio.fixture(name="basic_round")
async def _basic_round(basic_raceclass: RaceClass):
    async with Round.lock:
        value = await basic_raceclass.get_next_round_num()
        return await Round.create(raceclass=basic_raceclass, round_num=value)


@pytest_asyncio.fixture(name="basic_heat")
async def _basic_heat(basic_round: Round):
    async with Heat.lock:
        value = await basic_round.get_next_heat_num()
        return await Heat.create(round=basic_round, heat_num=value)


@pytest_asyncio.fixture(name="basic_slot")
async def _basic_slot(basic_heat: Heat):
    pilot = await Pilot.create(callsign="foo")
    return await Slot.create(heat=basic_heat, index=0, pilot=pilot)
