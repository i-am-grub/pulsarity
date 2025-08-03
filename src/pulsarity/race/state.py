"""
Race management
"""

import asyncio
import logging
from random import random

from pulsarity import ctx
from pulsarity.database.raceformat import RaceFormat
from pulsarity.events import RaceSequenceEvt, event_broker
from pulsarity.race.enums import RaceStatus

logger = logging.getLogger(__name__)

_RaceEventRecord = tuple[RaceStatus, float]


class RaceStateManager:
    """
    Manager for conducting races. Acts as a finite state
    machine.
    """

    _program_handle: asyncio.TimerHandle | None = None
    """The handle for managine the race sequence"""
    _status: RaceStatus = RaceStatus.READY
    """Internal status of the race"""
    _format: RaceFormat | None = None
    """The current race format"""

    def __init__(self) -> None:
        self._race_record: list[_RaceEventRecord] = []
        """The sequence of the race"""

    @property
    def status(self) -> RaceStatus:
        """The current status of the race"""
        return self._status

    @property
    def race_time(self) -> float:
        """
        The current time of the race

        :return: The race time or not
        """

        race_duration: float = 0.0
        race_period_start: float = 0.0
        last_status: RaceStatus | None = None

        if self.status in RaceStatus.PRERACE:
            return 0.0

        assert self._race_record, "Unexpected empty records"

        timestamp: float | None = None
        for status, timestamp in self._race_record:
            if status == RaceStatus.RACING:
                race_period_start = timestamp

            elif status == RaceStatus.OVERTIME:
                if last_status != RaceStatus.RACING:
                    race_period_start = timestamp

            elif status == RaceStatus.PAUSED:
                race_duration += timestamp - race_period_start

            elif status == RaceStatus.STOPPED:
                if last_status is not None and last_status in RaceStatus.UNDERWAY:
                    race_duration += timestamp - race_period_start
                return race_duration

            last_status = status

        assert timestamp is not None, (
            f"Unexpected state encountered: {self._race_record}"
        )

        if last_status == RaceStatus.PAUSED:
            return race_duration

        return race_duration + (ctx.loop_ctx.get().time() - timestamp)

    def get_race_start_time(self) -> float:
        """
        The start time of the race

        :raises RuntimeError: When race is not active
        :return: The start timestamp
        """
        for status, timestamp in self._race_record:
            if status == RaceStatus.RACING:
                return timestamp

        raise RuntimeError("Race not underway")

    def get_race_finish_time(self) -> float:
        """
        The finish time of the race

        :raises RuntimeError: When race is not active
        :return: The finish timestamp
        """
        for status, timestamp in self._race_record:
            if status in RaceStatus.FINISHED:
                return timestamp

        raise RuntimeError("Race not finished")

    def get_race_stop_time(self) -> float:
        """
        The stop time of the race

        :raises RuntimeError: When race is not active
        :return: The stop timestamp
        """
        for status, timestamp in self._race_record:
            if status == RaceStatus.STOPPED:
                return timestamp

        raise RuntimeError("Race not stopped")

    def _set_status(self, status: RaceStatus) -> None:
        """
        Set the current status of the race and create a record of
        status change

        :param status: _description_
        """
        self._status = status
        self._race_record.append((status, ctx.loop_ctx.get().time()))

    def schedule_race(
        self, format_: RaceFormat, *, assigned_start: float, **_kwargs
    ) -> None:
        """
        Schedule the sequence of events for the race

        :param format_: The race format to use
        :param assigned_start: The event loop start time of the race.
        Currently equivalent to monotonic time
        """
        if assigned_start < ctx.loop_ctx.get().time():
            raise ValueError("Assigned start is in the past")

        _random_delay = format_.random_stage_delay * random() * 0.001
        start_delay = format_.stage_time_sec + _random_delay
        start_time = assigned_start + start_delay

        if self.status == RaceStatus.READY:
            self._format = format_
            self._program_handle = ctx.loop_ctx.get().call_at(
                assigned_start, self._stage, start_time
            )
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

        if self.status in RaceStatus.PREPERATION:
            self._status = RaceStatus.READY
            self._race_record.clear()
            logger.info("Stopped race before start. Race manager reset")

        elif self.status == RaceStatus.RACING:
            data: dict = {}
            event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

        elif self.status == RaceStatus.OVERTIME:
            data = {}
            event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

        elif self.status == RaceStatus.PAUSED:
            for status, _ in reversed(self._race_record):
                if status in RaceStatus.UNDERWAY:
                    break
            else:
                raise RuntimeError("Underway status not found in paused race records")

            data = {}

            if status == RaceStatus.RACING:
                event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)
                event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)
            else:
                event_broker.trigger(RaceSequenceEvt.RACE_STOP, data)

            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

    def pause_race(self) -> None:
        """
        Pause the race
        """
        if self.status in RaceStatus.UNDERWAY:
            data: dict = {}
            event_broker.trigger(RaceSequenceEvt.RACE_PAUSE, data)
            self._set_status(RaceStatus.PAUSED)
            logger.info("Race paused")

            if self._program_handle is not None:
                self._program_handle.cancel()
                self._program_handle = None

    def resume_race(self) -> None:
        """
        Resme the race
        """
        if self.status != RaceStatus.PAUSED:
            return

        assert self._format is not None, "Can not resume race with an unset schedule"

        for status, _ in reversed(self._race_record):
            if status in RaceStatus.UNDERWAY:
                break
        else:
            raise RuntimeError("Underway status not found in paused race records")

        if self._format.unlimited_time:
            self._set_status(RaceStatus.RACING)

        elif (time_ := self.race_time) < self._format.race_time_sec:
            remaining_duration = self._format.race_time_sec - time_
            self._program_handle = ctx.loop_ctx.get().call_later(
                remaining_duration, self._finish
            )
            self._set_status(RaceStatus.RACING)

        else:
            remaining_duration = (
                self._format.race_time_sec + self._format.overtime_sec - time_
            )
            self._program_handle = ctx.loop_ctx.get().call_later(
                remaining_duration, self._stop
            )
            self._set_status(RaceStatus.OVERTIME)

        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_RESUME, data)
        logger.info("Race resumed")

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
        logger.info("Race scheduled for %d", start_time)

        self._program_handle = ctx.loop_ctx.get().call_at(start_time, self._start)

    def _start(self) -> None:
        """
        Put the system into race mode. Schedules the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        assert self._format is not None, "Can not start race with an unset schedule"

        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_START, data)
        self._set_status(RaceStatus.RACING)
        logger.info("Race started")

        if not self._format.unlimited_time:
            self._program_handle = ctx.loop_ctx.get().call_later(
                self._format.race_time_sec, self._finish
            )

        else:
            self._program_handle = None

    def _finish(self) -> None:
        """
        Put the system into overtime mode. Schedules or runs the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        assert self._format is not None, "Can not finish race with an unset schedule"

        data: dict = {}
        event_broker.trigger(RaceSequenceEvt.RACE_FINISH, data)

        if self._format.overtime_sec > 0:
            self._program_handle = ctx.loop_ctx.get().call_later(
                self._format.overtime_sec, self._stop
            )

            self._set_status(RaceStatus.OVERTIME)
            logger.info("Entering race overtime")

        elif self._format.overtime_sec == 0:
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
        logger.info("Race stopped")

    def reset(self) -> None:
        """
        Reset the manager for the next race
        """
        if self.status == RaceStatus.STOPPED:
            assert self._program_handle is None
            self._format = None
            self._race_record.clear()
            self._status = RaceStatus.READY
            logger.info("Race manager reset")


race_state_manager = RaceStateManager()
