"""
Race processor
"""

import inspect
from abc import ABC, abstractmethod
from collections import ChainMap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Callable, Generic, Self, TypedDict, TypeVar

from pulsarity import ctx
from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import ExtendedTimerData, TimerMode


class _BaseTypedDict(TypedDict):
    pass


T = TypeVar("T", bound=_BaseTypedDict)


@dataclass(frozen=True)
class SlotResult(Generic[T]):
    """
    Basic class for representing race data.

    Supported types for generic include dataclasses (preferred),
    dicts, lists, and tuples
    """

    slot_num: int
    position: int
    data: T

    def __lt__(self, other: Self):
        return self.position < other.position


class LapsManager(ABC):
    """
    Helper class to assist with storing lap data in `RaceProcessor`s

    This class automatically sorts lap data based on the timer mode and
    implements some convience equality methods to enable sorting. The
    structure of this class is largely based on using python tuple comparsions
    to allow for scoring across multiple variables in an order of importance
    """

    def __init__(self) -> None:
        self._primary_laps: dict[int, ExtendedTimerData] = {}
        self._split_laps: dict[int, ExtendedTimerData] = {}
        self._all_laps = ChainMap(self._primary_laps, self._split_laps)
        self._score: tuple | None = None

    def add_lap(self, key: int, lap: ExtendedTimerData) -> None:
        """
        Save a lap into the

        :param key: The key to save the lap with
        :param lap: The lap data
        """
        if lap.interface_mode == TimerMode.PRIMARY:
            self._score = None
            self._primary_laps[key] = lap
        elif lap.interface_mode == TimerMode.SPLIT:
            self._score = None
            self._split_laps[key] = lap
        else:
            raise ValueError("Unsupported TimerMode")

    def remove_lap(self, key: int) -> None:
        """
        Removes a saved lap

        :param key: The lap key
        :raises: `KeyError` when key not found
        """
        self._all_laps.pop(key)
        self._score = None

    def get_all_laps(self) -> Iterable[ExtendedTimerData]:
        """
        Get the lap data

        :return: The lap data
        """
        return self._all_laps.values()

    @abstractmethod
    def get_score(self) -> tuple:
        """
        Get the score tuple of the manager based on the currently stored
        lap data. This method should return the `self._store` cache if avaliable
        else build and return the cache.

        :return: A tuple of elements. The elements should be added to the tuple in
        order of conserideration.
        """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LapsManager):
            return False

        return self.get_score() == other.get_score()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, LapsManager):
            return True

        return self.get_score() != other.get_score()

    def __lt__(self, other: Self) -> bool:
        return self.get_score() < other.get_score()

    def __le__(self, other: Self) -> bool:
        return self.get_score() <= other.get_score()

    def __gt__(self, other: Self) -> bool:
        return self.get_score() > other.get_score()

    def __ge__(self, other: Self) -> bool:
        return self.get_score() >= other.get_score()


class RaceProcessor(ABC):
    """
    Abstract base class for processing race data.
    Can be used to enforce custom rulesets
    """

    @abstractmethod
    def __init__(self, race_format: RaceFormat) -> None:
        """
        Class initializer

        :param race_format: The active race format
        """

    @classmethod
    @abstractmethod
    def get_uid(cls) -> str:
        """
        Get the processor unique identifier
        """

    @abstractmethod
    def add_lap_record(self, slot: int, record: ExtendedTimerData) -> int:
        """
        Add lap record to the supervisor instance

        :param slot: The slot to assign the lap record
        :param record: The lap record to add
        :return: The key for the slot record
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
    def get_race_results(self) -> Sequence[SlotResult]:
        """
        Get the results of the race

        :return: An iterable of the results for all the slots
        """

    @abstractmethod
    def get_slot_result(self, slot_num: int) -> SlotResult | None:
        """
        Get the race results for a slot

        :param slot_num: The slot number
        :return: The results for the slot
        """

    @abstractmethod
    def get_laps(self) -> Iterable[ExtendedTimerData]:
        """
        Gets all of the laps stored by the race processor

        :return: An iterable of the lap data
        """


class RaceProcessorManager:
    """
    Manages the race processors
    """

    def __init__(self) -> None:
        self._registered_processors: dict[
            str | Callable[[RaceProcessor], str], type[RaceProcessor]
        ] = {}

    def register(self, processor_class: type[RaceProcessor]) -> type[RaceProcessor]:
        """
        Registers a rulesets type to be used by the system.
        Can be used as a decorator

        :param processor_class: The class to register
        :raises RuntimeError: Class already registered
        """

        if issubclass(processor_class, RaceProcessor) and not inspect.isabstract(
            processor_class
        ):
            uid = processor_class.get_uid()
            if uid in self._registered_processors:
                raise RuntimeError(
                    "Interface type with matching identifier already registered"
                )

            self._registered_processors[uid] = processor_class

            return processor_class

        raise TypeError(
            f"Attempted to register an invalid race processor: {processor_class.__name__}"
        )

    def get_processor(self, processor_uid: str) -> type[RaceProcessor] | None:
        """
        Gets the processor for the provided uid

        :param ruleset_uid: The uid of the processor
        :return:
        """
        return self._registered_processors.get(processor_uid)


def register_processor(interface_class: type[RaceProcessor]) -> type[RaceProcessor]:
    """
    Decorator used for registering RaceProcessor classes

    :param interface_class: The race processor class to register
    :return: The registered race processor
    """
    try:
        ctx.race_processor_ctx.get().register(interface_class)
    except LookupError:
        ...

    return interface_class
