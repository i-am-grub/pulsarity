"""
Race state/timing management
"""

import asyncio
from collections import defaultdict
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

from pulsarity.database.lap import Lap
from pulsarity.database.signal import SignalHistory
from pulsarity.race._state import RaceStateManager, RaceStatus
from pulsarity.race.ruleset import RaceRuleset, RaceRulesetManager, SafeRaceFormat

if TYPE_CHECKING:
    from pulsarity.database.raceformat import RaceFormat
    from pulsarity.interface.timer_manager import FullLapData, FullSignalData


class _SignalRecord(NamedTuple):
    timedelta: float
    value: float


class RaceManager:
    """
    Links race state/timing and race data
    """

    ___slots__ = ("_state", "_save_lock", "_signal_data", "_ruleset")

    def __init__(self) -> None:
        self._state = RaceStateManager()
        """The underlying race state manager"""
        self._save_lock = asyncio.Lock()
        """Save in progress lock"""
        self._signal_data: dict[int, dict[tuple[int, str], list[_SignalRecord]]] = (
            defaultdict(partial(defaultdict, list))
        )
        """Race signal data storage"""
        self._ruleset: RaceRuleset | None = None
        """The ruleset used for processing race data"""

    @property
    def status(self) -> RaceStatus:
        """The current status of the race"""
        return self._state.status

    @property
    def race_time(self) -> float:
        """
        The current time of the race
        """
        return self._state.race_time

    def get_race_start_time(self) -> float:
        """
        The start time of the race

        :raises RuntimeError: When race is not active
        :return: The start timestamp
        """
        return self._state.get_race_start_time()

    def get_race_finish_time(self) -> float:
        """
        The finish time of the race

        :raises RuntimeError: When race is not active
        :return: The finish timestamp
        """
        return self._state.get_race_finish_time()

    def get_race_stop_time(self) -> float:
        """
        The stop time of the race

        :raises RuntimeError: When race is not active
        :return: The stop timestamp
        """
        return self._state.get_race_stop_time()

    def schedule_race(self, format_: RaceFormat, *, assigned_start: float):
        """
        Schedule the sequence of events for the race

        :param format_: The race format to use
        :param assigned_start: The event loop start time of the race.
        Currently equivalent to monotonic time
        """
        ruleset = RaceRulesetManager.get_ruleset(format_.ruleset_id)
        safe_format = SafeRaceFormat.from_format(format_)
        self._ruleset = ruleset(safe_format)
        self._state.schedule_race(safe_format, assigned_start=assigned_start)

    def stop_race(self) -> None:
        """
        Stop the race
        """
        self._state.stop_race()

    def pause_race(self) -> None:
        """
        Pause the race
        """
        self._state.pause_race()

    async def reset(self) -> None:
        """
        Reset the manager for the next race. The reset can only occur
        when the race has been stopped.

        `WARNING`: This will clear all unsaved data
        """
        if self._state.status is RaceStatus.STOPPED:
            async with self._save_lock:
                self._state.reset()
                self._ruleset = None
                self._signal_data.clear()

    def add_lap_record(self, slot: int, record: FullLapData) -> None:
        """
        Add lap record to the ruleset instance

        :param slot: Slot to assign the lap record
        :param lap_data: Lap data
        """
        if self._ruleset is not None:
            self._ruleset.add_lap_record(slot, record)
        else:
            msg = "Unable to add record when ruleset is not set"
            raise RuntimeError(msg)

    def status_aware_lap_record(self, slot: int, record: FullLapData) -> None:
        """
        Add a lap record to the ruleset instance if the race status is underway

        :param slot: The slot to add the lap record to
        :param record: The lap record to add
        """
        if self.status in RaceStatus.UNDERWAY:
            self.add_lap_record(slot, record)

    def add_signal_record(self, record: FullSignalData) -> None:
        """
        Add a signal record to the race manager

        :param record: The signal record to store
        """
        key = (record.timer_index, record.timer_identifier)
        record_ = _SignalRecord(record.timedelta, record.value)
        self._signal_data[record.node_index][key].append(record_)

    def status_aware_signal_record(self, record: FullSignalData) -> None:
        """
        Add a signal record to the race manager if the race status is underway

        :param record: The signal record to store
        """
        if self.status in RaceStatus.UNDERWAY:
            self.add_signal_record(record)

    def remove_lap_record(self, slot: int, key: int) -> None:
        """
        Add remove record from the ruleset instance

        :param slot: Slot to assign the lap record
        :param key: The key to use for removing the record
        """
        if self._ruleset is not None:
            try:
                self._ruleset.remove_lap_record(slot, key)
            except KeyError as ex:
                msg = "Invalid value for lap key"
                raise ValueError(msg) from ex
        else:
            msg = "Unable to remove record when ruleset is not set"
            raise RuntimeError(msg)

    async def _save_lap_data(self) -> None:
        """
        Saves the lap data to the database
        """
        if self._ruleset is not None:
            laps = (
                Lap(
                    slot_id=lap.node_index,
                    time=timedelta(seconds=lap.timedelta),
                    timer_index=lap.timer_index,
                    timer_identifier=lap.timer_identifier,
                )
                for lap in self._ruleset.get_laps_iterable()
            )
            await Lap.bulk_create(laps, batch_size=25)
        else:
            msg = "Unable to save laps when process is not set"
            raise RuntimeError(msg)

    async def _save_signal_data(self) -> None:
        """
        Saves the signal history to the database
        """

        def get_slot_data():
            for slot, data_ in self._signal_data.items():
                for (idx, ident), data in data_.items():
                    data.sort()
                    yield SignalHistory(
                        slot_id=slot,
                        timer_index=idx,
                        timer_identifier=ident,
                        history=data,
                    )

        if self._signal_data:
            await SignalHistory.bulk_create(get_slot_data(), batch_size=5)

    async def save_race_data(self) -> None:
        """
        Saves the race data to the database
        """
        if self._state.status is RaceStatus.STOPPED:
            async with self._save_lock, asyncio.TaskGroup() as tg:
                tg.create_task(self._save_lap_data())
                tg.create_task(self._save_signal_data())
