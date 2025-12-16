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
from pulsarity.utils import background
from pulsarity.utils.config import get_configs_defaults
from pulsarity.webserver import generate_application


@pytest_asyncio.fixture(autouse=True)
async def context_and_cleanup():
    loop = asyncio.get_running_loop()
    ctx.loop_ctx.set(loop)

    yield

    await background.shutdown(5)


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
        transport=transport, base_url="https://localhost"
    ) as client_:
        yield client_


@pytest.fixture(name="user_creds")
def default_user_creds():
    configs = get_configs_defaults()

    username = str(configs["SECRETS"]["DEFAULT_USERNAME"])
    password = str(configs["SECRETS"]["DEFAULT_PASSWORD"])

    yield username, password


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
