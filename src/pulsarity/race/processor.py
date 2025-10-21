"""
Race processor
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import ExtendedTimerData

T = TypeVar("T")


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


@runtime_checkable
class RaceProcessor(Protocol):
    """
    Protocol for processing race data. Can be used to enforce
    custom rulesets
    """

    uid: str
    """Processor unique identifier"""

    def __init__(self, race_format: RaceFormat) -> None:
        """
        Class initializer

        :param race_format: The active race format
        """

    def add_lap_record(self, slot: int, record: ExtendedTimerData) -> None:
        """
        Add lap record to the supervisor instance

        :param slot: Slot to assign the lap record
        :param lap_data: Lap data
        """

    def remove_lap_record(self, slot: int, index: int) -> None:
        """
        Remove lap record from the supervisor instance

        :param slot: Slot where the lap record is stored
        :param index: The index of the slot lap record
        """

    def is_slot_done(self, slot_num: int) -> bool:
        """
        Check if the slot has finished

        :param slot_num: number
        :return: Done status
        """

    def get_race_results(self) -> Iterable[SlotResult]:
        """
        Get the results of the race

        :return: An iterable of the results for all the slots
        """

    def get_slot_results(self, slot_num: int) -> SlotResult:
        """
        Get the race results for a slot

        :param slot_num: The slot number
        :return: The results for the slot
        """


_registered_processors: dict[str, type[RaceProcessor]] = {}


def register_processor(processor_class: type[RaceProcessor]) -> type[RaceProcessor]:
    """
    Registers a rulesets type to be used by the system.
    Can be used as a decorator

    :param processor_class: The class to register
    :raises RuntimeError: Class already registered
    """

    if isinstance(processor_class, RaceProcessor):
        if processor_class.uid in _registered_processors:
            raise RuntimeError(
                "Interface type with matching identifier already registered"
            )

        _registered_processors[processor_class.uid] = processor_class

        return processor_class

    raise RuntimeError("Attempted to register an invalid race processor class")


def get_processor(ruleset_uid: str) -> type[RaceProcessor] | None:
    """
    Gets the processor for the provided uid

    :param ruleset_uid: The uid of the processor
    :return:
    """
    return _registered_processors.get(ruleset_uid)
