import asyncio
import time

import pytest

from pulsarity.database import RaceSchedule
from pulsarity.race.enums import RaceStatus
from pulsarity.race.manager import RaceManager
from pulsarity.utils.background import background_tasks


def future_schedule(limited_schedule_: RaceSchedule, race_manager: RaceManager):
    schedule_offset = 1
    schedule_time = time.monotonic() + schedule_offset

    race_manager.schedule_race(limited_schedule_, assigned_start=schedule_time)

    return schedule_offset


@pytest.mark.asyncio
async def test_default_status(race_manager: RaceManager):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    assert race_manager.status == RaceStatus.READY
    race_manager.stop_race()
    assert race_manager.status == RaceStatus.READY

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_past_schedule(limited_schedule: RaceSchedule, race_manager: RaceManager):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    assert race_manager.status == RaceStatus.READY

    now = time.monotonic() - 0.1

    with pytest.raises(ValueError):
        race_manager.schedule_race(limited_schedule, assigned_start=now)

    assert race_manager.status == RaceStatus.READY

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_limited_sequence(
    limited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(limited_schedule, race_manager)

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

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_scheduled_stopped(
    limited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_staging_stopped(
    limited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_racing_stopped(
    limited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_overtime_stopped(
    limited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_no_overtime(
    limited_no_ot_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(limited_no_ot_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_no_ot_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_no_ot_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)


@pytest.mark.asyncio
async def test_unlimited_sequence(
    unlimited_schedule: RaceSchedule, race_manager: RaceManager
):
    loop = asyncio.get_running_loop()
    background_tasks.set_event_loop(loop)

    offset = future_schedule(unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(unlimited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.RACING
    assert race_manager._program_handle is None

    await background_tasks.shutdown(5)
