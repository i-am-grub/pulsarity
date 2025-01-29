"""
Race management
"""

import logging
import asyncio
from typing import TYPE_CHECKING
from random import random
from collections.abc import Generator

from quart import copy_current_app_context

from .enums import RaceStatus
from ..events import RaceSequenceEvt
from ..database.race._orm.raceformat import RaceSchedule
from ..utils.eager_task import schedule_eager_task, delay_eager_task

if TYPE_CHECKING:
    from ..extensions import current_app
else:
    from quart import current_app

logger = logging.getLogger(__name__)


class RaceManager:
    """
    Manager for conducting races
    """

    _program_handle: asyncio.TimerHandle | None = None
    status: RaceStatus = RaceStatus.READY

    def _staging_checks(self, assigned_start: float) -> Generator[bool, None, None]:
        yield self.status == RaceStatus.READY
        yield self._program_handle is None

        loop = asyncio.get_running_loop()
        yield loop.time() < assigned_start

    def schedule_race(self, schedule: RaceSchedule, assigned_start: float) -> None:
        """
        Schedule the sequence of events for the race

        :param format_: The race format to use
        :param assigned_start: The event loop start time of the race.
        Currently equivalent to monotonic time
        """

        @copy_current_app_context
        async def _stage() -> None:
            data: dict = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_STAGE, data)
            self.status = RaceStatus.STAGING
            self._program_handle = schedule_eager_task(
                assigned_start + start_delay, _start(), loop=loop, block_duration=0.05
            )

            logger.debug(
                "Staging completed at %s seconds after assigned start",
                loop.time() - assigned_start,
            )

        @copy_current_app_context
        async def _start() -> None:
            data: dict = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_START, data)
            self.status = RaceStatus.RACING

            if not schedule.unlimited_time:
                self._program_handle = delay_eager_task(
                    schedule.race_time_sec, _finish(), loop=loop, block_duration=0.05
                )
            else:
                self._program_handle = None

        @copy_current_app_context
        async def _finish() -> None:
            data: dict = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
            self.status = RaceStatus.OVERTIME

            if schedule.overtime_sec > 0:
                self._program_handle = delay_eager_task(
                    schedule.overtime_sec, _stop(), loop=loop, block_duration=0.05
                )
            elif schedule.overtime_sec == 0:
                await _stop()
            else:
                self._program_handle = None

        @copy_current_app_context
        async def _stop() -> None:
            data: dict = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self.status = RaceStatus.STOPPED
            self._program_handle = None

        loop = asyncio.get_running_loop()
        _random_delay = schedule.random_stage_delay * random() * 0.001
        start_delay = schedule.stage_time_sec + _random_delay

        if all(self._staging_checks(assigned_start)):
            self._program_handle = schedule_eager_task(
                assigned_start, _stage(), loop=loop, block_duration=0.05
            )
            self.status = RaceStatus.SCHEDULED

        else:
            logger.warning("All conditions are not met to program race")

    def stop_race(self) -> None:
        """
        Stop the race
        """

        if self._program_handle is not None:
            self._program_handle.cancel()
            self._program_handle = None

        if self.status in (RaceStatus.SCHEDULED, RaceStatus.STAGING):
            self.status = RaceStatus.READY

        elif self.status == RaceStatus.RACING:
            data: dict = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self.status = RaceStatus.STOPPED

        elif self.status == RaceStatus.OVERTIME:
            data = {}
            current_app.event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self.status = RaceStatus.STOPPED
