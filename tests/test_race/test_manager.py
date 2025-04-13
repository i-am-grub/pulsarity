import asyncio
import time

import pytest

from pulsarity.database import RaceSchedule
from pulsarity.extensions import PulsarityApp
from pulsarity.race.enums import RaceStatus
from pulsarity.race.manager import RaceManager


async def future_schedule(
    app_: PulsarityApp, limited_schedule_: RaceSchedule, race_manager: RaceManager
):
    schedule_offset = 1
    schedule_time = time.monotonic() + schedule_offset

    async with app_.app_context():
        race_manager.schedule_race(limited_schedule_, assigned_start=schedule_time)

    return schedule_offset


async def cancel_race(app_: PulsarityApp, race_manager: RaceManager):

    async with app_.app_context():
        await race_manager.stop_race()


@pytest.mark.asyncio
async def test_default_status(race_manager: RaceManager):
    assert race_manager.status == RaceStatus.READY
    race_manager.stop_race()
    assert race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_past_schedule(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):
    assert race_manager.status == RaceStatus.READY

    now = time.monotonic() - 0.1

    with pytest.raises(ValueError):
        async with app.app_context():
            race_manager.schedule_race(limited_schedule, assigned_start=now)

    assert race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_limited_sequence(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset)

    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    await asyncio.sleep(limited_schedule.overtime_sec)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_scheduled_stopped(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):

    await future_schedule(app, limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await cancel_race(app, race_manager)

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_staging_stopped(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    await cancel_race(app, race_manager)

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_racing_stopped(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await cancel_race(app, race_manager)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_overtime_stopped(
    app: PulsarityApp, limited_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    await cancel_race(app, race_manager)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_no_overtime(
    app: PulsarityApp, limited_no_ot_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, limited_no_ot_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_no_ot_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_no_ot_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_unlimited_sequence(
    app: PulsarityApp, unlimited_schedule: RaceSchedule, race_manager: RaceManager
):

    offset = await future_schedule(app, unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(unlimited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.RACING
    assert race_manager._program_handle is None
