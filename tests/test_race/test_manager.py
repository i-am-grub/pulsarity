import pytest
import time
import asyncio

from prophazard.extensions import RHApplication
from prophazard.race.enums import RaceStatus
from prophazard.database.race._orm.raceformat import RaceSchedule


async def future_schedule(app_: RHApplication, limited_schedule_: RaceSchedule):
    app_.race_manager.status = RaceStatus.READY  # Manually reset this for testing

    schedule_offset = 1
    schedule_time = time.monotonic() + schedule_offset

    async with app_.app_context():
        app_.race_manager.schedule_race(limited_schedule_, schedule_time)

    return schedule_offset


async def cancel_race(app_: RHApplication):

    async with app_.app_context():
        app_.race_manager.stop_race()


@pytest.mark.asyncio
async def test_default_status(app: RHApplication):
    assert app.race_manager.status == RaceStatus.READY
    app.race_manager.stop_race() == RaceStatus.READY
    assert app.race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_past_schedule(app: RHApplication, limited_schedule: RaceSchedule):
    assert app.race_manager.status == RaceStatus.READY

    now = time.monotonic()

    async with app.app_context():
        app.race_manager.schedule_race(limited_schedule, now)

    assert app.race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_limited_sequence(app: RHApplication, limited_schedule: RaceSchedule):

    offset = await future_schedule(app, limited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset)

    assert app.race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert app.race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert app.race_manager.status == RaceStatus.OVERTIME

    await asyncio.sleep(limited_schedule.overtime_sec)

    assert app.race_manager.status == RaceStatus.STOPPED
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_scheduled_stopped(app: RHApplication, limited_schedule: RaceSchedule):

    await future_schedule(app, limited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await cancel_race(app)

    assert app.race_manager.status == RaceStatus.READY
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_staging_stopped(app: RHApplication, limited_schedule: RaceSchedule):

    offset = await future_schedule(app, limited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert app.race_manager.status == RaceStatus.STAGING

    await cancel_race(app)

    assert app.race_manager.status == RaceStatus.READY
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_racing_stopped(app: RHApplication, limited_schedule: RaceSchedule):

    offset = await future_schedule(app, limited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert app.race_manager.status == RaceStatus.RACING

    await cancel_race(app)

    assert app.race_manager.status == RaceStatus.STOPPED
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_overtime_stopped(app: RHApplication, limited_schedule: RaceSchedule):

    offset = await future_schedule(app, limited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert app.race_manager.status == RaceStatus.OVERTIME

    await cancel_race(app)

    assert app.race_manager.status == RaceStatus.STOPPED
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_no_overtime(app: RHApplication, limited_no_ot_schedule: RaceSchedule):

    offset = await future_schedule(app, limited_no_ot_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_no_ot_schedule.stage_time_sec)

    assert app.race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_no_ot_schedule.race_time_sec)

    assert app.race_manager.status == RaceStatus.STOPPED
    assert app.race_manager._program_handle is None


@pytest.mark.asyncio
async def test_unlimited_sequence(app: RHApplication, unlimited_schedule: RaceSchedule):

    offset = await future_schedule(app, unlimited_schedule)

    assert app.race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert app.race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert app.race_manager.status == RaceStatus.RACING

    await asyncio.sleep(unlimited_schedule.race_time_sec)

    assert app.race_manager.status == RaceStatus.RACING
    assert app.race_manager._program_handle is None
