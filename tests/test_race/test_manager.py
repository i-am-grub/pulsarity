import asyncio
import time

import pytest
import pytest_asyncio

from pulsarity.database import RaceFormat
from pulsarity.race.enums import RaceStatus
from pulsarity.race.state import RaceStateManager
from pulsarity.utils import background

# pylint: disable=W0212


@pytest_asyncio.fixture(name="race_manager", loop_scope="function")
async def _race_manager():
    """
    Setup the RaceStateManager and shutdown background tasks
    """
    # pylint: disable=W0613
    yield RaceStateManager()


def future_schedule(limited_schedule_: RaceFormat, race_manager: RaceStateManager):
    """
    Schedules a race 1 second into the future
    """

    schedule_offset = 1
    schedule_time = time.monotonic() + schedule_offset

    race_manager.schedule_race(limited_schedule_, assigned_start=schedule_time)

    return schedule_offset


@pytest.mark.asyncio
async def test_default_status(race_manager: RaceStateManager):
    """
    Test stopping a race when a race isn't running
    """
    assert race_manager.status == RaceStatus.READY
    race_manager.stop_race()
    assert race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_past_schedule(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test scheduling a race that was set to start in the past
    """
    assert race_manager.status == RaceStatus.READY

    now = time.monotonic() - 0.1

    with pytest.raises(ValueError):
        race_manager.schedule_race(limited_schedule, assigned_start=now)

    assert race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_limited_sequence(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test a full race sequenece with limited time schedule
    """
    assert race_manager.status == RaceStatus.READY

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

    race_manager.reset()
    assert race_manager.status == RaceStatus.READY


@pytest.mark.asyncio
async def test_scheduled_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test scheduling a race and stopping it before it started
    """
    future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None

    await background.shutdown(1)


@pytest.mark.asyncio
async def test_staging_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test stopping a staging race
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.READY
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_racing_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test stopping running race
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_overtime_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Test stopping running race in overtime
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    race_manager.stop_race()

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_no_overtime(
    race_manager: RaceStateManager, limited_no_ot_schedule: RaceFormat
):
    """
    Test running a race schedule that doesn't have overtime
    """
    offset = future_schedule(limited_no_ot_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_no_ot_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_no_ot_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_unlimited_sequence(
    race_manager: RaceStateManager, unlimited_schedule: RaceFormat
):
    """
    Test running a race schedule that doesn't stop the race automatically
    after the race completes
    """
    offset = future_schedule(unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(unlimited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.RACING
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_racing_paused(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Tests pausing the race while the race is running
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    race_manager.pause_race()

    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager._program_handle is None

    time_ = race_manager.race_time
    assert time_ > 0.0
    await asyncio.sleep(0.1)
    new_time = race_manager.race_time
    assert time_ == new_time

    race_manager.resume_race()
    await asyncio.sleep(0.1)
    newest_time = race_manager.race_time
    assert race_manager.status == RaceStatus.RACING
    assert newest_time > time_


@pytest.mark.asyncio
async def test_overtime_paused(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Tests pausing the race when it has entered overtime
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    race_manager.pause_race()

    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager._program_handle is None

    time_ = race_manager.race_time
    assert time_ > 0.0
    await asyncio.sleep(0.1)
    new_time = race_manager.race_time
    assert time_ == new_time

    race_manager.resume_race()
    await asyncio.sleep(0.1)
    newest_time = race_manager.race_time
    assert race_manager.status == RaceStatus.OVERTIME
    assert newest_time > time_


@pytest.mark.asyncio
async def test_unlimited_sequence_resume(
    race_manager: RaceStateManager, unlimited_schedule: RaceFormat
):
    """
    Tests resuming a race after it has been paused while racing
    """
    offset = future_schedule(unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    race_manager.pause_race()

    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager._program_handle is None

    time_ = race_manager.race_time
    assert time_ > 0
    await asyncio.sleep(0.1)
    new_time = race_manager.race_time
    assert time_ == new_time

    race_manager.resume_race()
    await asyncio.sleep(0.1)
    newest_time = race_manager.race_time
    assert race_manager.status == RaceStatus.RACING
    assert newest_time > time_


@pytest.mark.asyncio
async def test_racing_paused_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Tests stopping a race after it has been paused
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING

    race_manager.pause_race()

    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager._program_handle is None

    time_ = race_manager.race_time
    assert time_ > 0
    await asyncio.sleep(0.1)
    new_time = race_manager.race_time
    assert time_ == new_time

    race_manager.stop_race()
    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_overtime_paused_stopped(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Stopping a race after it was paused in overtime
    """

    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset + 0.1)

    await asyncio.sleep(limited_schedule.stage_time_sec)

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME

    race_manager.pause_race()

    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager._program_handle is None

    time_ = race_manager.race_time
    assert time_ > 0.0
    await asyncio.sleep(0.1)
    new_time = race_manager.race_time
    assert time_ == new_time

    race_manager.stop_race()
    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None


@pytest.mark.asyncio
async def test_limited_sequence_pause_resume_fail(
    race_manager: RaceStateManager, limited_schedule: RaceFormat
):
    """
    Tests pausing a race after the race has been stopped
    """
    offset = future_schedule(limited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED

    race_manager.pause_race()
    assert race_manager.status == RaceStatus.SCHEDULED
    race_manager.resume_race()
    assert race_manager.status == RaceStatus.SCHEDULED

    await asyncio.sleep(offset)

    assert race_manager.status == RaceStatus.STAGING

    race_manager.pause_race()
    assert race_manager.status == RaceStatus.STAGING
    race_manager.resume_race()
    assert race_manager.status == RaceStatus.STAGING

    await asyncio.sleep(limited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING
    race_manager.resume_race()
    assert race_manager.status == RaceStatus.RACING

    await asyncio.sleep(limited_schedule.race_time_sec)

    assert race_manager.status == RaceStatus.OVERTIME
    race_manager.resume_race()
    assert race_manager.status == RaceStatus.OVERTIME

    await asyncio.sleep(limited_schedule.overtime_sec)

    assert race_manager.status == RaceStatus.STOPPED
    assert race_manager._program_handle is None

    race_manager.pause_race()
    assert race_manager.status == RaceStatus.STOPPED
    race_manager.resume_race()
    assert race_manager.status == RaceStatus.STOPPED


@pytest.mark.asyncio
async def test_get_race_start(
    race_manager: RaceStateManager, unlimited_schedule: RaceFormat
):
    """
    Tests the race time increments at race start
    """
    offset = future_schedule(unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED
    with pytest.raises(RuntimeError):
        race_manager.get_race_start_time()

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING
    with pytest.raises(RuntimeError):
        race_manager.get_race_start_time()

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING
    assert race_manager.race_time > 0.0


@pytest.mark.asyncio
async def test_get_race_time(
    race_manager: RaceStateManager, unlimited_schedule: RaceFormat
):
    """
    Tests the race time increments with state
    """

    offset = future_schedule(unlimited_schedule, race_manager)

    assert race_manager.status == RaceStatus.SCHEDULED
    assert race_manager.race_time == 0.0

    await asyncio.sleep(offset + 0.1)

    assert race_manager.status == RaceStatus.STAGING
    assert race_manager.race_time == 0.0

    await asyncio.sleep(unlimited_schedule.stage_time_sec)

    assert race_manager.status == RaceStatus.RACING
    assert race_manager.race_time > 0.0

    race_manager.pause_race()
    pause_time = race_manager.race_time
    assert race_manager.status == RaceStatus.PAUSED
    assert race_manager.race_time > 0.0
    await asyncio.sleep(1)
    assert race_manager.race_time == pause_time

    race_manager.stop_race()
    assert race_manager.status == RaceStatus.STOPPED
    await asyncio.sleep(1)
    assert race_manager.race_time > 0.0
    assert race_manager.race_time == pause_time
