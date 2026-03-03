"""
Most laps implementation
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from itertools import count
from typing import TypedDict

from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import FullLapData
from pulsarity.race.processor import (
    LapsManager,
    RaceProcessor,
    SlotResult,
    register_processor,
)
from pulsarity.utils.collections import ValueSortedDict


class _ResultExtras(TypedDict):
    """
    Temporary result extra definition
    """

    total_laps: int


class _MostLapsManager(LapsManager):
    """
    Lap data manager for a single slot
    """

    __slots__ = ("_primary_laps", "_split_laps", "_all_laps", "_score")

    def __init__(self):
        super().__init__()
        self._score = None

    def add_lap_cb(self, *_) -> None:
        self._score = None

    def remove_lap_cb(self, *_) -> None:
        self._score = None

    def get_score(self) -> tuple:
        """
        Return from cache or build slot score based on the following order:
        - Primary laps completed
        - Index of the timer who recorded the last split lap that proceeds
        the last recorded primary lap
        - The timestamp of the last recorded lap
        (inverted to make smaller timestamps ranked higher)

        :return: The tuple containing the score
        """

        if self._score is not None:
            return self._score

        primary_laps = 0
        last_index = 0
        last_timestamp = 0.0

        if self._primary_laps:
            primary_laps = len(self._primary_laps)
            last_lap = self._primary_laps.peek_value(-1)
            last_timestamp = last_lap.timedelta

        if self._split_laps:
            last_split = self._split_laps.peek_value(-1)

            if last_split.timedelta > last_timestamp:
                last_index = last_split.timer_index
                last_timestamp = last_split.timedelta

        self._score = (primary_laps, last_index, -last_timestamp)

        return self._score


@register_processor
class MostLapsProcessor(RaceProcessor):
    """
    Processor to enforce the most laps ruleset
    """

    __slots__ = ("_format", "_lap_data", "_cache", "_count")
    _uid = "most_laps"

    def __init__(self, race_format: RaceFormat) -> None:
        self._format = race_format
        self._lap_data: dict[int, _MostLapsManager] = defaultdict(_MostLapsManager)
        self._cache: ValueSortedDict[int, SlotResult[_ResultExtras]] = ValueSortedDict()
        self._count = count()

    @classmethod
    def get_uid(cls) -> str:
        return cls._uid

    def add_lap_record(self, slot: int, record: FullLapData) -> int | None:
        if (
            self._format.overtime_sec == 0
            and record.timedelta >= self._format.race_time_sec
        ):
            return None

        id_ = next(self._count)
        self._lap_data[slot].add_lap(id_, record)
        self._cache.clear()
        return id_

    def remove_lap_record(self, slot: int, key: int) -> None:
        self._lap_data[slot].remove_lap(key)
        self._cache.clear()

    def is_slot_done(self, slot_num: int) -> bool:
        slot_data = self._lap_data[slot_num]

        last_lap = slot_data.get_last_primary_lap()
        if last_lap is not None:
            return last_lap.timedelta > self._format.race_time_sec

        return False

    def _get_cache(self) -> ValueSortedDict[int, SlotResult[_ResultExtras]]:
        if not self._cache:
            slot_data = [(value, slot_id) for slot_id, value in self._lap_data.items()]
            slot_data.sort(reverse=True)

            pos, step = 0, 1
            last_manager: _MostLapsManager | None = None
            for manager, slot_id in slot_data:
                if manager == last_manager:
                    step += 1
                else:
                    pos += step
                    step = 1

                result = SlotResult(
                    pos, slot_id, _ResultExtras(total_laps=manager.get_num_laps())
                )
                self._cache[slot_id] = result
                last_manager = manager

        return self._cache

    def get_race_results(self) -> Sequence[SlotResult[_ResultExtras]]:
        return tuple(self._get_cache().values())

    def get_slot_result(self, slot_num: int) -> SlotResult[_ResultExtras] | None:
        return self._get_cache().get(slot_num, None)

    def get_laps(self) -> Iterable[FullLapData]:
        for slot in self._lap_data.values():
            yield from slot.get_all_laps()
