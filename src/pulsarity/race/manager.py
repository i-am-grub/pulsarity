"""
Race management
"""

import asyncio
import logging
from collections.abc import Generator
from random import random

from ..database.raceformat import RaceSchedule
from ..events import RaceSequenceEvt, event_broker
from .enums import RaceStatus

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

    def schedule_race(
        self, schedule: RaceSchedule, *, assigned_start: float, **_kwargs
    ) -> None:
        """
        Schedule the sequence of events for the race

        :param format_: The race format to use
        :param assigned_start: The event loop start time of the race.
        Currently equivalent to monotonic time
        """
        loop = asyncio.get_running_loop()
        if assigned_start < loop.time():
            raise ValueError("Assigned start is in the past")

        _random_delay = schedule.random_stage_delay * random() * 0.001
        start_delay = schedule.stage_time_sec + _random_delay
        start_time = assigned_start + start_delay

        if all(self._staging_checks(assigned_start)):
            self._program_handle = loop.call_at(
                assigned_start, self._stage, start_time, schedule
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
            event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self.status = RaceStatus.STOPPED

        elif self.status == RaceStatus.OVERTIME:
            data = {}
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self.status = RaceStatus.STOPPED

    def _stage(self, start_time: float, schedule: RaceSchedule) -> None:
        """
        Put the system into staging mode and schedules the start
        state.

        :param start_time: The time to start to schedule race start
        :param schedule: The format's race schedule
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_STAGE, data)
        self.status = RaceStatus.STAGING

        self._program_handle = asyncio.get_running_loop().call_at(
            start_time, self._start, schedule
        )

    def _start(self, schedule: RaceSchedule) -> None:
        """
        Put the system into race mode. Schedules the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_START, data)
        self.status = RaceStatus.RACING

        if not schedule.unlimited_time:
            self._program_handle = asyncio.get_running_loop().call_later(
                schedule.race_time_sec, self._finish, schedule
            )

        else:
            self._program_handle = None

    def _finish(self, schedule: RaceSchedule) -> None:
        """
        Put the system into overtime mode. Schedules or runs the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
        self.status = RaceStatus.OVERTIME

        if schedule.overtime_sec > 0:
            self._program_handle = asyncio.get_running_loop().call_later(
                schedule.overtime_sec, self._stop
            )

        elif schedule.overtime_sec == 0:
            self._stop()

        else:
            self._program_handle = None

    def _stop(self) -> None:
        """
        Put the system into race stop mode
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
        self.status = RaceStatus.STOPPED

        self._program_handle = None


race_manager = RaceManager()
