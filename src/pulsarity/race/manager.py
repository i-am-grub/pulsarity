"""
Race state/timing management
"""

from pulsarity import ctx
from pulsarity.database.raceformat import RaceFormat
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

    def __init__(self):
        self._state = RaceStateManager()
        """The underlying race state manager"""

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

    def reset(self) -> None:
        """
        Reset the manager for the next race
        """
        self._state.reset()
        self._processor = None

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

        event_broker = ctx.event_broker_ctx.get()

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

        event_broker = ctx.event_broker_ctx.get()
