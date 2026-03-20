"""
Race management
"""

import logging
from enum import Flag, auto
from random import random
from typing import TYPE_CHECKING, NamedTuple

from pulsarity import ctx
from pulsarity.events import RaceSequenceEvt

if TYPE_CHECKING:
    from asyncio import TimerHandle

    from pulsarity.race.ruleset import SafeRaceFormat

logger = logging.getLogger(__name__)


class RaceStatus(Flag):
    """
    Current status of system.
    """

    READY = auto()
    """Ready to start a new race, no race running"""
    SCHEDULED = auto()
    """The race is scheduled to occur"""
    STAGING = auto()
    """System is staging; Race begins imminently"""
    RACING = auto()
    """Racing is underway"""
    OVERTIME = auto()
    """The duration of the race has been exceeded; Racing is still underway"""
    PAUSED = auto()
    """Racing is paused"""
    STOPPED = auto()
    """System no longer listening for lap crossings; Race results must be saved or discarded"""
    UNDERWAY = RACING | OVERTIME
    """Shortcut for `RACING` or `OVERTIME`"""
    FINISHED = OVERTIME | STOPPED
    """Shortcut for `OVERTIME` or `STOPPED`"""
    SUSPENDED = READY | SCHEDULED | STAGING | PAUSED | STOPPED
    """Shortcut for a race not being actively underway"""
    PRERACE = READY | SCHEDULED | STAGING
    """Shortcut for pre-race statuses"""
    PREPERATION = SCHEDULED | STAGING
    """Shortcut for race preperation statuses"""


class _RaceEventRecord(NamedTuple):
    status: RaceStatus
    timestamp: float


class RaceStateManager:
    """
    Manager for conducting races. Acts as a finite state
    machine.
    """

    __slots__ = ("_format", "_program_handle", "_race_records", "_status")

    def __init__(self) -> None:
        self._race_records: list[_RaceEventRecord] = []
        """The sequence of the race"""
        self._program_handle: TimerHandle | None = None
        """The handle for managine the race sequence"""
        self._status: RaceStatus = RaceStatus.READY
        """Internal status of the race"""
        self._format: SafeRaceFormat | None = None
        """The current race format"""

    @property
    def status(self) -> RaceStatus:
        """The current status of the race"""
        return self._status

    @property
    def race_time(self) -> float:
        """
        The current time of the race

        :return: The race time
        """
        if self.status in RaceStatus.PRERACE:
            return 0.0

        if not self._race_records:
            msg = "Unexpected empty records"
            raise RuntimeError(msg)

        race_duration: float = 0.0
        race_period_start: float = 0.0
        last_status: RaceStatus | None = None

        timestamp: float | None = None
        for status, timestamp in self._race_records:
            if status is RaceStatus.RACING:
                race_period_start = timestamp

            elif status is RaceStatus.OVERTIME:
                if last_status != RaceStatus.RACING:
                    race_period_start = timestamp

            elif status is RaceStatus.PAUSED:
                race_duration += timestamp - race_period_start

            elif status is RaceStatus.STOPPED:
                if last_status is not None and last_status in RaceStatus.UNDERWAY:
                    race_duration += timestamp - race_period_start
                return race_duration

            last_status = status

        if timestamp is None:
            msg = f"Unexpected state encountered: {self._race_records}"
            raise RuntimeError(msg)

        if last_status is RaceStatus.PAUSED:
            return race_duration

        return race_duration + (ctx.loop_ctx.get().time() - timestamp)

    def get_race_start_time(self) -> float:
        """
        The start time of the race

        :raises RuntimeError: When race is not active
        :return: The start timestamp
        """
        for record in self._race_records:
            if record.status is RaceStatus.RACING:
                return record.timestamp
        msg = "Race not underway"
        raise RuntimeError(msg)

    def get_race_finish_time(self) -> float:
        """
        The finish time of the race

        :raises RuntimeError: When race is not active
        :return: The finish timestamp
        """
        for record in self._race_records:
            if record.status in RaceStatus.FINISHED:
                return record.timestamp
        msg = "Race not finished"
        raise RuntimeError(msg)

    def get_race_stop_time(self) -> float:
        """
        The stop time of the race

        :raises RuntimeError: When race is not active
        :return: The stop timestamp
        """
        for record in self._race_records:
            if record.status is RaceStatus.STOPPED:
                return record.timestamp
        msg = "Race not stopped"
        raise RuntimeError(msg)

    def _set_status(self, status: RaceStatus) -> None:
        """
        Set the current status of the race and create a record of
        status change

        :param status: The status to set the the manager to
        """
        self._status = status
        self._race_records.append(_RaceEventRecord(status, ctx.loop_ctx.get().time()))

    def schedule_race(self, format_: SafeRaceFormat, assigned_start: float) -> None:
        """
        Schedule the sequence of events for the race

        :param format_: The race format to use
        :param assigned_start: The event loop start time of the race.
        Currently equivalent to monotonic time
        """
        if assigned_start < ctx.loop_ctx.get().time():
            msg = "Assigned start is in the past"
            raise ValueError(msg)

        _random_delay = format_.random_stage_delay * random() * 0.001  # noqa: S311
        start_delay = format_.stage_time_sec + _random_delay
        start_time = assigned_start + start_delay

        if self.status is RaceStatus.READY:
            self._format = format_
            self._program_handle = ctx.loop_ctx.get().call_at(
                assigned_start, self._stage, start_time
            )
            self._set_status(RaceStatus.SCHEDULED)

        else:
            msg = "Unable to resume race state when race status is not paused"
            raise RuntimeError(msg)

    def stop_race(self) -> None:
        """
        Stop the race
        """
        event_broker = ctx.event_broker_ctx.get()

        if self._program_handle is not None:
            self._program_handle.cancel()
            self._program_handle = None

        if self.status in RaceStatus.PREPERATION:
            self._status = RaceStatus.READY
            self._race_records.clear()
            logger.info("Stopped race before start. Race manager reset")

        elif self.status is RaceStatus.RACING:
            event_broker.trigger_background(RaceSequenceEvt.RACE_FINISH)
            event_broker.trigger_background(RaceSequenceEvt.RACE_STOP)
            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

        elif self.status is RaceStatus.OVERTIME:
            event_broker.trigger_background(RaceSequenceEvt.RACE_STOP)
            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

        elif self.status is RaceStatus.PAUSED:
            for record in reversed(self._race_records):
                if record.status in RaceStatus.UNDERWAY:
                    break
            else:
                msg = "Underway status not found in paused race records"
                raise RuntimeError(msg)

            if record.status is RaceStatus.RACING:
                event_broker.trigger_background(RaceSequenceEvt.RACE_FINISH)
                event_broker.trigger_background(RaceSequenceEvt.RACE_STOP)
            else:
                event_broker.trigger_background(RaceSequenceEvt.RACE_STOP)

            self._set_status(RaceStatus.STOPPED)
            logger.info("Race stopped")

    def pause_race(self) -> None:
        """
        Pause the race
        """
        event_broker = ctx.event_broker_ctx.get()

        if self.status in RaceStatus.UNDERWAY:
            event_broker.trigger_background(RaceSequenceEvt.RACE_PAUSE)
            self._set_status(RaceStatus.PAUSED)
            logger.info("Race paused")

            if self._program_handle is not None:
                self._program_handle.cancel()
                self._program_handle = None

    def resume_race(self) -> None:
        """
        Resme the race
        """
        event_broker = ctx.event_broker_ctx.get()

        if self.status is not RaceStatus.PAUSED:
            msg = "Unable to resume a race state when race status is not paused"
            raise RuntimeError(msg)

        if self._format is None:
            msg = "Can not resume a race with an unset schedule"
            raise RuntimeError(msg)

        for record in reversed(self._race_records):
            if record.status in RaceStatus.UNDERWAY:
                break
        else:
            msg = "Underway status not found in paused race records"
            raise RuntimeError(msg)

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

        event_broker.trigger_background(RaceSequenceEvt.RACE_RESUME)
        logger.info("Race resumed")

    def _stage(self, start_time: float) -> None:
        """
        Put the system into staging mode and schedules the start
        state.

        :param start_time: The time to start to schedule race start
        :param schedule: The format's race schedule
        """
        event_broker = ctx.event_broker_ctx.get()

        event_broker.trigger_background(RaceSequenceEvt.RACE_STAGE)
        self._set_status(RaceStatus.STAGING)
        logger.info("Race scheduled for %d", start_time)

        self._program_handle = ctx.loop_ctx.get().call_at(start_time, self._start)

    def _start(self) -> None:
        """
        Put the system into race mode. Schedules the next
        state if applicable.

        :param schedule: The format's race schedule
        """
        event_broker = ctx.event_broker_ctx.get()
        if self._format is None:
            msg = "Can not start a race with an unset schedule"
            raise RuntimeError(msg)

        event_broker.trigger_background(RaceSequenceEvt.RACE_START)
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
        event_broker = ctx.event_broker_ctx.get()
        if self._format is None:
            msg = "Can not finish a race with an unset schedule"
            raise RuntimeError(msg)

        event_broker.trigger_background(RaceSequenceEvt.RACE_FINISH)

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
        event_broker = ctx.event_broker_ctx.get()

        event_broker.trigger_background(RaceSequenceEvt.RACE_STOP)
        self._set_status(RaceStatus.STOPPED)
        self._program_handle = None
        logger.info("Race stopped")

    def reset(self) -> None:
        """
        Reset the manager for the next race
        """
        if self.status is RaceStatus.STOPPED:
            self._format = None
            self._race_records.clear()
            self._status = RaceStatus.READY
            logger.info("Race manager reset")
        else:
            msg = "Unable to reset race state when race status is not stopped"
            raise RuntimeError(msg)
