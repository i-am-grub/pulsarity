"""
Race management
"""

import asyncio
import logging
from random import random

from ..database.raceformat import RaceSchedule
from ..events import RaceSequenceEvt, event_broker
from .enums import RaceStatus

logger = logging.getLogger(__name__)

_RaceEventRecord = tuple[RaceStatus, float]


class RaceManager:
    """
    Manager for conducting races
    """

    _program_handle: asyncio.TimerHandle | None = None
    """The handle for managine the race sequence"""
    _status: RaceStatus = RaceStatus.READY
    """Internal status of the race"""
    _schedule: RaceSchedule | None = None
    """The current race schedule"""

    def __init__(self) -> None:
        self._race_record: list[_RaceEventRecord] = []
        """The sequence of the race"""

    @property
    def status(self) -> RaceStatus:
        """The current status of the race"""
        return self._status

    def get_race_start_time(self) -> float:
        """
        The start time of the race

        :raises Runti: _description_
        :return: _description_
        :yield: _description_
        """
        for record in self._race_record:
            if record[0] == RaceStatus.RACING:
                return record[1]

        raise RuntimeError("Race not underway")

    def get_race_time(self) -> float:
        """
        The current time of the race

        :return: The race time or not
        """
        # pylint: disable=W0631

        race_duration: float = 0
        race_period_start: float = 0
        last_status: RaceStatus | None = None

        if self.status in (RaceStatus.SCHEDULED, RaceStatus.STAGING, RaceStatus.READY):
            raise RuntimeError("Race has not begun")

        assert self._race_record, "Unable to retrive time from empty record"

        for record in self._race_record:
            recorded_status = record[0]

            if recorded_status == RaceStatus.RACING:
                race_period_start = record[0]

            elif recorded_status == RaceStatus.OVERTIME:
                if last_status != RaceStatus.RACING:
                    race_period_start = record[0]

            elif recorded_status == RaceStatus.PAUSED:
                race_duration += record[1] - race_period_start

            elif recorded_status == RaceStatus.STOPPED:
                if last_status != RaceStatus.PAUSED:
                    race_duration += record[1] - race_period_start
                return race_duration

            last_status = recorded_status

        if last_status == RaceStatus.PAUSED:
            return race_duration

        loop = asyncio.get_running_loop()
        return race_duration + (loop.time() - record[1])

    def _set_status(self, status: RaceStatus) -> None:
        """
        Set the current status of the race and create a record of
        status change

        :param status: _description_
        """
        self._status = status
        loop = asyncio.get_running_loop()
        self._race_record.append((status, loop.time()))

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

        if self.status == RaceStatus.READY:
            assert self._program_handle is None, "A program handle is already active"
            assert loop.time() < assigned_start, "Assigned start not in the future"

            self._schedule = schedule
            self._program_handle = loop.call_at(assigned_start, self._stage, start_time)
            self._set_status(RaceStatus.SCHEDULED)

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
            self._status = RaceStatus.READY
            self._race_record.clear()

        elif self.status == RaceStatus.RACING:
            data: dict = {}
            event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self._set_status(RaceStatus.STOPPED)

        elif self.status == RaceStatus.OVERTIME:
            data = {}
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self._set_status(RaceStatus.STOPPED)

        elif self.status == RaceStatus.PAUSED:
            for record in reversed(self._race_record):
                status = record[0]

                if status in (RaceStatus.RACING, RaceStatus.OVERTIME):
                    data = {}

                    if status == RaceStatus.RACING:
                        event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
                        event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
                    else:
                        event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)

                    self._set_status(RaceStatus.STOPPED)
                    break

    def pause_race(self) -> None:
        """
        Pause the race
        """
        if self.status in (RaceStatus.RACING, RaceStatus.OVERTIME):
            data: dict = {}
            event_broker.trigger(RaceSequenceEvt.RACE_PAUSE, data)
            self._set_status(RaceStatus.PAUSED)

    def resume_race(self) -> None:
        """
        Resme the race
        """
        if self.status == RaceStatus.PAUSED:

            assert (
                self._schedule is not None
            ), "Can not resume race with an unset schedule"

            for record in reversed(self._race_record):
                status = record[0]

                if status in (RaceStatus.RACING, RaceStatus.OVERTIME):

                    if self._schedule.unlimited_time:
                        self._set_status(RaceStatus.RACING)

                    elif (time_ := self.get_race_time()) < self._schedule.race_time_sec:
                        remaining_duration = self._schedule.race_time_sec - time_
                        self._program_handle = asyncio.get_running_loop().call_later(
                            remaining_duration, self._finish
                        )
                        self._set_status(RaceStatus.RACING)

                    else:
                        remaining_duration = (
                            self._schedule.race_time_sec
                            + self._schedule.overtime_sec
                            - time_
                        )
                        self._program_handle = asyncio.get_running_loop().call_later(
                            remaining_duration, self._stop
                        )
                        self._set_status(RaceStatus.OVERTIME)

                    data: dict = {}
                    event_broker.trigger(RaceSequenceEvt.RACE_RESUME, data)

                    break

    def _stage(self, start_time: float) -> None:
        """
        Put the system into staging mode and schedules the start
        state.

        :param start_time: The time to start to schedule race start
        :param schedule: The format's race schedule
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_STAGE, data)
        self._set_status(RaceStatus.STAGING)

        self._program_handle = asyncio.get_running_loop().call_at(
            start_time, self._start
        )

    def _start(self) -> None:
        """
        Put the system into race mode. Schedules the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        assert self._schedule is not None, "Can not start race with an unset schedule"

        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_START, data)
        self._set_status(RaceStatus.RACING)

        if not self._schedule.unlimited_time:
            self._program_handle = asyncio.get_running_loop().call_later(
                self._schedule.race_time_sec, self._finish
            )

        else:
            self._program_handle = None

    def _finish(self) -> None:
        """
        Put the system into overtime mode. Schedules or runs the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        assert self._schedule is not None, "Can not finish race with an unset schedule"

        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
        self._set_status(RaceStatus.OVERTIME)

        if self._schedule.overtime_sec > 0:
            self._program_handle = asyncio.get_running_loop().call_later(
                self._schedule.overtime_sec, self._stop
            )

        elif self._schedule.overtime_sec == 0:
            self._stop()

        else:
            self._program_handle = None

    def _stop(self) -> None:
        """
        Put the system into race stop mode
        """
        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
        self._set_status(RaceStatus.STOPPED)

        self._program_handle = None

    def reset(self) -> None:
        """
        Reset the manager for the next race
        """
        if self.status == RaceStatus.STOPPED:
            assert self._program_handle is None
            self._schedule = None
            self._race_record.clear()
            self._status = RaceStatus.READY


race_manager = RaceManager()
