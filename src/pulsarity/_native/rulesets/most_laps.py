"""
Most laps implementation
"""

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import count
from typing import final

from pulsarity.api.ruleset import (
    CombinedMetrics,
    LapsManager,
    RaceRuleset,
    RulesetCustomFields,
    RulesetMeta,
    SlotResult,
    SoloResultData,
    register_ruleset,
)


@final
class _MostLapsManager(LapsManager):
    """
    Lap data manager for a single slot
    """

    __slots__ = ("_metrics", "_score")

    def __init__(self):
        super().__init__()
        self._score = None
        self._metrics = None

    def add_lap_cb(self, *_) -> None:
        self._score = None
        self._metrics = None

    def remove_lap_cb(self, *_) -> None:
        self._score = None
        self._metrics = None

    def get_metrics(
        self,
        holeshot: bool = False,
        consec_laps: int = 3,
    ) -> CombinedMetrics | None:
        """
        Gets the combined metrics

        :param holeshot: Holeshot active, defaults to False
        :param consec_laps: The max consecutive laps, defaults to 3
        :return: The generated metrics
        """
        if self._metrics is None:
            self._metrics = self.get_combined_metrics(holeshot, consec_laps)
        return self._metrics

    def get_score(self):
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
        last_timestamp = float("inf")

        if self._primary_laps:
            primary_laps = len(self._primary_laps)
            last_lap = self._primary_laps.values()[-1]
            last_timestamp = last_lap.millis

        if self._split_laps:
            last_split = self._split_laps.values()[-1]

            if last_split.millis > last_timestamp:
                last_index = last_split.timer_index
                last_timestamp = last_split.millis

        self._score = (primary_laps, last_index, -last_timestamp)

        return self._score


@final
@dataclass(frozen=True, slots=True)
class _MostLapsFields(RulesetCustomFields):
    """
    Fields for MostLapsRuleset
    """

    holeshot: bool = field(default=False, metadata={"display_name": "Holeshot"})
    consecutive: int = field(default=3, metadata={"display_name": "Consecutive Laps"})


@register_ruleset
@final
class MostLapsRuleset(RaceRuleset[_MostLapsFields, SoloResultData]):
    """
    ruleset to enforce the most laps ruleset
    """

    __slots__ = ("_cache", "_count", "_format", "_lap_data", "_race_time_millis")

    __meta__ = RulesetMeta(uid="most_laps", fields=_MostLapsFields)

    def __init__(self, race_format) -> None:
        self._format = race_format
        self._lap_data: dict[int, _MostLapsManager] = defaultdict(_MostLapsManager)
        self._cache: dict[int, SlotResult[SoloResultData]] = {}
        self._count = count()
        self._race_time_millis = self._format.race_time_sec * 1000

    def add_lap_record(self, slot, record):
        if self._format.overtime_sec == 0 and record.millis >= self._race_time_millis:
            return None

        id_ = next(self._count)
        self._lap_data[slot].add_lap(id_, record)
        self._cache.clear()
        return id_

    def remove_lap_record(self, slot, key) -> None:
        self._lap_data[slot].remove_lap(key)
        self._cache.clear()

    def is_slot_done(self, slot_num):
        slot_data = self._lap_data[slot_num]
        last_lap = slot_data.get_last_primary_lap()
        if last_lap is not None:
            return last_lap.millis > self._race_time_millis
        return False

    def all_slots_finished(self):
        return all(self.is_slot_done(slot) for slot in self._lap_data)

    def _get_cache(self) -> dict[int, SlotResult[SoloResultData]]:
        """
        Reads from the cache; if it doesn't exist, build it first.
        Makes use of the `_MostLapsManager`'s ability to be sorted
        against itself by each instance's current score.
        """
        if self._cache:
            return self._cache

        sorted_slots = sorted(
            self._lap_data.items(), key=lambda pair: pair[1], reverse=True
        )

        pos, step = 0, 1
        prev_manager: _MostLapsManager | None = None

        for slot_id, manager in sorted_slots:
            if manager == prev_manager:
                step += 1
            else:
                pos += step
                step = 1

            metrics = manager.get_metrics(
                self._format.fields.holeshot, self._format.fields.consecutive
            )

            result: SlotResult[SoloResultData]
            if metrics:
                result = SlotResult(pos, (slot_id,), SoloResultData(*metrics))
            else:
                result = SlotResult(pos, (slot_id,), None)

            self._cache[slot_id] = result
            prev_manager = manager

        return self._cache

    def get_race_results(self):
        return tuple(self._get_cache().values())

    def get_slot_result(self, slot_num):
        return self._get_cache().get(slot_num, None)

    def get_laps_iterable(self):
        for slot in self._lap_data.values():
            yield from slot.get_all_laps_iterable()
