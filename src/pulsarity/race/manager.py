"""
Race state/timing management
"""

import asyncio
from collections import defaultdict
from datetime import timedelta

from pulsarity import ctx
from pulsarity.database.lap import Lap
from pulsarity.database.raceformat import RaceFormat
from pulsarity.database.signal import SignalHistory
from pulsarity.interface.timer_manager import ExtendedTimerData
from pulsarity.race._state import RaceStateManager
from pulsarity.race.enums import RaceStatus
from pulsarity.race.processor import RaceProcessor


class RaceManager:
    """
    Links race state/timing and race data
    """

    _processor: RaceProcessor | None = None
    """The processor used for processing race data"""

    def __init__(self) -> None:
        self._state = RaceStateManager()
        """The underlying race state manager"""
        self._save_lock = asyncio.Lock()
        """Save in progress lock"""
        self._signal_data: dict[int, dict[int, list[ExtendedTimerData]]] = defaultdict(
            lambda: defaultdict(list)
        )
        """Race signal data storage"""

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
        processor_manager = ctx.race_processor_ctx.get()
        processor = processor_manager.get_processor(format_.processor_id)

        if processor is None:
            raise ValueError("Processor with witching id not found")

        self._state.schedule_race(format_, assigned_start=assigned_start)
        self._processor = processor(format_)

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

        `WARNING`: This will clear all data (including unsaved)
        """
        if self._state.status == RaceStatus.STOPPED:
            async with self._save_lock:
                self._state.reset()
                self._processor = None
                self._signal_data.clear()

    def add_lap_record(self, slot: int, record: ExtendedTimerData) -> None:
        """
        Add lap record to the processor instance

        :param slot: Slot to assign the lap record
        :param lap_data: Lap data
        """
        if self._processor is not None:
            self._processor.add_lap_record(slot, record)
        else:
            raise RuntimeError("Unable to add record when processor is not set")

    def remove_lap_record(self, slot: int, key: int) -> None:
        """
        Add remove record from the processor instance

        :param slot: Slot to assign the lap record
        :param key: The key to use for removing the record
        """
        if self._processor is not None:
            try:
                self._processor.remove_lap_record(slot, key)
            except KeyError as ex:
                raise ValueError("Invalid value for lap key") from ex
        else:
            raise RuntimeError("Unable to remove record when processor is not set")

    def status_aware_lap_record(self, slot: int, record: ExtendedTimerData) -> None:
        """
        Add a lap record to the processor instance if the race status is underway

        :param slot: _description_
        :param record: _description_
        """
        if self.status in RaceStatus.UNDERWAY:
            assert self._processor is not None
            self._processor.add_lap_record(slot, record)

    def status_aware_signal_record(self, record: ExtendedTimerData) -> None:
        """
        Add a lap record to the processor instance if the race status is underway

        :param slot: _description_
        :param record: _description_
        """
        if self.status in RaceStatus.UNDERWAY:
            self._signal_data[record.node_index][record.interface_index].append(record)

    async def _save_lap_data(self) -> None:
        """
        Saves the lap data to the database
        """
        if self._processor is not None:
            laps = (
                Lap(
                    slot_id=lap.node_index,
                    time=timedelta(seconds=lap.timestamp),
                    mode=lap.interface_mode,
                )
                for lap in self._processor.get_laps()
            )
            await Lap.bulk_create(laps, batch_size=25)
        else:
            raise RuntimeError("Unable to save laps when process is not set")

    async def _save_signal_data(self) -> None:
        """
        Saves the lap data to the database
        """

        def get_slot_data():
            for slot, _data in self._signal_data.items():
                for idx, data in _data.items():
                    history = [(timedelta(seconds=x.timestamp), x.value) for x in data]

                    yield SignalHistory(
                        slot_id=slot,
                        timer_index=idx,
                        timer_identifier=data[0].timer_identifier,
                        timer_mode=data[0].interface_mode,
                        history=history,
                    )

        if self._signal_data:
            await SignalHistory.bulk_create(get_slot_data(), batch_size=5)

    async def save_race_data(self) -> None:
        """
        Saves the race data to the database
        """
        if self._state.status == RaceStatus.STOPPED:
            async with self._save_lock, asyncio.TaskGroup() as tg:
                tg.create_task(self._save_lap_data())
                tg.create_task(self._save_signal_data())
