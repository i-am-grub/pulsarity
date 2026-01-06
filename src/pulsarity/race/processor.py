"""
Race processor
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from pulsarity import ctx
from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import ExtendedTimerData

T = TypeVar("T", bound=dict)


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

    def add_lap_record(self, slot: int, record: ExtendedTimerData) -> int:
        """
        Add lap record to the supervisor instance

        :param slot: Slot to assign the lap record
        :param lap_data: Lap data
        :return: The key for the slot record
        """

    def remove_lap_record(self, slot: int, key: int) -> None:
        """
        Remove lap record from the supervisor instance

        :param slot: Slot where the lap record is stored
        :param key: The key of the slot lap record
        :raises: `KeyError` when key not found
        """

    def is_slot_done(self, slot_num: int) -> bool:
        """
        Check if the slot has finished

        :param slot_num: number
        :return: Done status
        """

    def get_race_results(self) -> Sequence[SlotResult]:
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
        self._registered_processors: dict[str, type[RaceProcessor]] = {}

    def register(self, processor_class: type[RaceProcessor]) -> type[RaceProcessor]:
        """
        Registers a rulesets type to be used by the system.
        Can be used as a decorator

        :param processor_class: The class to register
        :raises RuntimeError: Class already registered
        """

        if isinstance(processor_class, RaceProcessor):
            if processor_class.uid in self._registered_processors:
                raise RuntimeError(
                    "Interface type with matching identifier already registered"
                )

            self._registered_processors[processor_class.uid] = processor_class

            return processor_class

        raise RuntimeError("Attempted to register an invalid race processor class")

    def get_processor(self, ruleset_uid: str) -> type[RaceProcessor] | None:
        """
        Gets the processor for the provided uid

        :param ruleset_uid: The uid of the processor
        :return:
        """
        return self._registered_processors.get(ruleset_uid)


def register_processor(interface_class: type[RaceProcessor]) -> type[RaceProcessor]:
    """
    Decorator used for registering RaceProcessor classes

    :param interface_class: The race processor class to register
    :return: The registered race processor
    """
    ctx.race_processor_ctx.get().register(interface_class)
    return interface_class
