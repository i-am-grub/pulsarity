"""
Race ruleset
"""

from __future__ import annotations

import inspect
import logging
from abc import ABC, abstractmethod
from collections import ChainMap
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    ClassVar,
    NamedTuple,
    Self,
)

from pulsarity.race import metrics
from pulsarity.timing_interface.timer_manager import FullLapData, TimerMode
from pulsarity.utils.collections import ValueSortedDict

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from _typeshed import SupportsAllComparisons, SupportsBool

    from pulsarity.database._base import JsonParsable
    from pulsarity.database.raceformat import RaceFormat


logger = logging.getLogger(__name__)


class SafeRaceFormat(NamedTuple):
    """
    Immutable for holding race format data
    """

    stage_time_sec: int
    random_stage_delay: int
    unlimited_time: bool
    race_time_sec: int
    overtime_sec: int
    fields: dict[str, JsonParsable]

    @classmethod
    def from_format(cls, format_: RaceFormat) -> Self:
        """
        Builds an immutable from the a database race format instance and
        the ruleset fields default values.
        """
        ruleset = RaceRulesetManager.get_ruleset(format_.ruleset_id)
        fields = {field.name: field.default for field in ruleset.__meta__.fields}
        fields.update({field.name: field.value for field in format_.ruleset_fields})
        return cls(
            format_.stage_time_sec,
            format_.random_stage_delay,
            format_.unlimited_time,
            format_.race_time_sec,
            format_.overtime_sec,
            fields,
        )


@dataclass(frozen=True, slots=True)
class SlotResult[T]:
    """
    Basic class for representing race data.

    Supported types for generic include dataclasses (preferred)
    and dicts
    """

    position: int
    """result position"""
    slots: Sequence[int]
    """contributing slots"""
    data: T | None = None
    """additional data"""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlotResult):
            return False
        return self.position == other.position

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, SlotResult):
            return True
        return self.position != other.position

    def __lt__(self, other: Self) -> bool:
        return self.position < other.position

    def __le__(self, other: Self) -> bool:
        return self.position <= other.position

    def __gt__(self, other: Self) -> bool:
        return self.position > other.position

    def __ge__(self, other: Self) -> bool:
        return self.position >= other.position

    def __hash__(self):
        return object.__hash__(self)


class LapsManager(ABC):
    """
    Helper class to assist with storing lap data in `Raceruleset`s

    This class automatically sorts lap data based on the `TimerMode` and
    implements convience comparsion methods to enable sorting based on the
    returned value by the `get_score` method (defined by the child inheriting
    from this class).
    """

    __slots__ = ("_all_laps", "_primary_laps", "_split_laps")

    def __init__(self) -> None:
        self._primary_laps: ValueSortedDict[int, FullLapData] = ValueSortedDict()
        self._split_laps: ValueSortedDict[int, FullLapData] = ValueSortedDict()
        self._all_laps: ChainMap[int, FullLapData] = ChainMap(
            self._primary_laps,
            self._split_laps,
        )

    def __len__(self) -> int:
        """
        The number of **primary** laps registered to the manager. This
        also enables the `__bool__` evaluation.
        """
        return self._primary_laps.__len__()

    def add_lap(self, key: int, lap: FullLapData) -> None:
        """
        Save a lap into the manager. Does not check if lap
        key already exists within manager,

        :param key: The key to save the lap with
        :param lap: The lap data
        """
        if lap.timer_mode is TimerMode.PRIMARY:
            self._primary_laps[key] = lap
        else:
            self._split_laps[key] = lap
        self.add_lap_cb(key, lap)

    def remove_lap(self, key: int) -> None:
        """
        Removes a saved lap

        :param key: The lap key
        :raises: `KeyError` when key not found
        """
        for map_ in self._all_laps.maps:
            try:
                lap = map_.pop(key)
            except KeyError:
                continue
            break
        else:
            msg = "Key not stored in manager"
            raise KeyError(msg)

        self.remove_lap_cb(key, lap)

    def get_all_laps(self) -> Sequence[FullLapData]:
        """
        Gets all lap data. When planning to only iterate over
        the data, consider using `get_all_laps_iterable` for
        computational efficency instead.

        :return: A sequence of lap data
        """
        return tuple(self._all_laps.values())

    def get_all_laps_iterable(self) -> Iterable[FullLapData]:
        """
        Gets an iterable that provides all lap data.

        :return: The lap data iterable
        """
        yield from self._all_laps.values()

    def get_last_primary_lap(self) -> FullLapData | None:
        """
        Get the lap data from the last primary lap

        :return: The lap data
        """
        if self._primary_laps:
            return self._primary_laps.values()[-1]
        return None

    def get_num_laps(self, holeshot: bool = False) -> int:
        """
        Get number of laps completed

        :param holeshot: Holeshot active, defaults to False
        :return: The number of laps completed
        """
        return metrics.calculate_num_laps(self._primary_laps.values(), holeshot)

    def get_total_time(self, holeshot: bool = False) -> float:
        """
        Get the total time

        :param holeshot: Holeshot active, defaults to False
        :return: The total time
        """
        return metrics.calculate_total_time(self._primary_laps.values(), holeshot)

    def get_average_lap_time(self, holeshot: bool = False) -> float | None:
        """
        Get the average lap time

        :param holeshot: Holeshot active, defaults to False
        :return: The average time
        """
        return metrics.calculate_average_lap_time(self._primary_laps.values(), holeshot)

    def get_fastest_time(self, holeshot: bool = False) -> float | None:
        """
        Get the fastest lap time

        :param holeshot: Holeshot active, defaults to False
        :return: The time associated with the fastest lap
        """
        return metrics.calculate_fastest_time(self._primary_laps.values(), holeshot)

    def get_fastest_consecutive_metric(
        self,
        holeshot: bool = False,
        consec_laps: int = 3,
    ) -> metrics.ConsecutiveMetric | None:
        """
        Get the fastest consecutive lap times

        Uses `get_combined_metrics` to generate the metrics
        due to most of its logic is allocated to efficiently
        calculate fastest consecutive time.

        :param holeshot: Holeshot active, defaults to False
        :param max_laps: The max consecutive laps, defaults to 3
        :return: A tuple of number of laps and the time associated with the laps
        """
        return metrics.calculate_fastest_consecutive_metric(
            self._primary_laps.values(), holeshot, consec_laps
        )

    def get_combined_metrics(
        self,
        holeshot: bool = False,
        consec_laps: int = 3,
    ) -> metrics.CombinedMetrics | None:
        """
        Generate multiple metrics at once.

        Includes the following:
        - number of laps completed
        - total time
        - average lap time
        - fastest lap time
        - consecutive lap base
        - fastest consecutive lap time

        :param holeshot: Holeshot active, defaults to False
        :param max_laps: The max consecutive laps, defaults to 3
        :return: The generated metrics
        """
        return metrics.calculate_combined_metrics(
            self._primary_laps.values(), holeshot, consec_laps
        )

    @abstractmethod
    def add_lap_cb(self, key: int, lap: FullLapData) -> None:
        """
        Callback for a lap being added to the manager

        :param key: The key for the lap
        :param lap: The added lap
        """

    @abstractmethod
    def remove_lap_cb(self, key: int, lap: FullLapData) -> None:
        """
        Callback for a lap being removed from the manager

        :param key: The key for the lap
        :param lap: The removed lap
        """

    @abstractmethod
    def get_score(self) -> SupportsAllComparisons:
        """
        Get the score of the manager based on the currently stored
        lap data.

        It is recommended to return a tuple to allow for scoring
        across multiple parameters in an order of significance
        (See tuple comparsions in Python)
        """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LapsManager):
            return False
        return self.get_score() == other.get_score()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, LapsManager):
            return True
        return self.get_score() != other.get_score()

    def __lt__(self, other: Self) -> SupportsBool:
        return self.get_score() < other.get_score()

    def __le__(self, other: Self) -> SupportsBool:
        return self.get_score() <= other.get_score()

    def __gt__(self, other: Self) -> SupportsBool:
        return self.get_score() > other.get_score()

    def __ge__(self, other: Self) -> SupportsBool:
        return self.get_score() >= other.get_score()

    def __hash__(self):
        return object.__hash__(self)


class RulesetFieldData[T: JsonParsable](NamedTuple):
    """
    Custom field data for ruleset
    """

    name: str
    display_name: str
    type_: type[T]
    default: T


class RulesetMeta(NamedTuple):
    """
    Ruleset metadata
    """

    uid: str
    """ruleset unique identifier"""
    fields: Iterable[RulesetFieldData]
    """custom fields for ruleset"""


@dataclass(frozen=True, slots=True)
class ResultData:
    """
    Abstract class defining race result data (used for typing)
    """


@dataclass(frozen=True, slots=True)
class SoloResultData(ResultData):
    """
    Basic class for representing solo pilot race data.
    """

    total_laps: int
    total_time: float
    average_lap_time: float
    fastest_time: float
    fastest_consec_base: int
    fastest_consec_time: float


class RaceRuleset[T: ResultData](ABC):
    """
    Abstract base class for processing race data.
    Can be used to enforce custom rulesets
    """

    __meta__: RulesetMeta

    @abstractmethod
    def __init__(self, race_format: SafeRaceFormat) -> None:
        """
        Class initializer

        :param race_format: The active race format
        """

    @abstractmethod
    def add_lap_record(self, slot: int, record: FullLapData) -> int | None:
        """
        Add lap record to the supervisor instance

        :param slot: The slot to assign the lap record
        :param record: The lap record to add
        :return: The key for the slot record or None if the record was not added
        """

    @abstractmethod
    def remove_lap_record(self, slot: int, key: int) -> None:
        """
        Remove lap record from the supervisor instance

        :param slot: Slot where the lap record is stored
        :param key: The key of the slot lap record
        :raises: `KeyError` when key not found
        """

    @abstractmethod
    def is_slot_done(self, slot_num: int) -> bool:
        """
        Check if the slot has finished

        :param slot_num: number
        :return: Done status
        """

    @abstractmethod
    def all_slots_finished(self) -> bool:
        """
        Check if all the slots have finished

        :return: Finished status
        """

    @abstractmethod
    def get_race_results(self) -> Sequence[SlotResult[T]]:
        """
        Get the results of the race

        :return: An iterable of the results for all the slots
        """

    @abstractmethod
    def get_slot_result(self, slot_num: int) -> SlotResult[T] | None:
        """
        Get the race results for a slot

        :param slot_num: The slot number
        :return: The results for the slot
        """

    @abstractmethod
    def get_laps_iterable(self) -> Iterable[FullLapData]:
        """
        Gets all of the laps stored by the race ruleset

        :return: An iterable of the lap data
        """


class RaceRulesetManager:
    """
    Manages the race rulesets
    """

    _registered_ruleset: ClassVar[
        dict[str | Callable[[RaceRuleset], str], type[RaceRuleset]],
    ] = {}

    @classmethod
    def register(cls, ruleset_class: type[RaceRuleset]) -> type[RaceRuleset]:
        """
        Registers a rulesets type to be used by the system.
        Can be used as a decorator

        :param ruleset_class: The class to register
        :raises RuntimeError: Class already registered
        """

        if issubclass(ruleset_class, RaceRuleset):
            if inspect.isabstract(ruleset_class):
                msg = "Attempted to register an abstract race ruleset"
                raise TypeError(msg)

            uid = ruleset_class.__meta__.uid
            if uid in cls._registered_ruleset:
                msg = "Interface type with matching identifier already registered"
                raise RuntimeError(msg)

            cls._registered_ruleset[uid] = ruleset_class

            return ruleset_class

        msg = f"Attempted to register an invalid race ruleset: {ruleset_class.__name__}"
        raise TypeError(msg)

    @classmethod
    def get_ruleset(cls, ruleset_uid: str) -> type[RaceRuleset]:
        """
        Gets the ruleset for the provided uid

        :param ruleset_uid: The uid of the ruleset
        :return:
        """
        try:
            return cls._registered_ruleset[ruleset_uid]
        except KeyError:
            logger.exception(
                "ruleset for format is not registered in the system. Key id: %s",
                ruleset_uid,
            )
            raise

    @classmethod
    def clear_registered(cls) -> None:
        """
        UNIT TESTING ONLY: Clears all registered rulesets.
        """
        cls._registered_ruleset.clear()


def register_ruleset(interface_class: type[RaceRuleset]) -> type[RaceRuleset]:
    """
    Decorator used for registering Raceruleset classes

    :param interface_class: The race ruleset class to register
    :return: The registered race ruleset
    """
    RaceRulesetManager.register(interface_class)
    return interface_class
