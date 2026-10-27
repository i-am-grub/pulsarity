"""
Race ruleset
"""

from __future__ import annotations

import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    NamedTuple,
    Self,
    override,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from pulsarity._core.database.raceformat import RaceFormat
    from pulsarity._core.timing_interface.timer_manager import FullLapData


logger = logging.getLogger(__name__)


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

    @override
    def __eq__(self, other: object):
        if isinstance(other, SlotResult):
            return self.position == other.position
        return NotImplemented

    @override
    def __ne__(self, other: object):
        if isinstance(other, SlotResult):
            return self.position != other.position
        return NotImplemented

    def __lt__(self, other: Self) -> bool:
        return self.position < other.position

    def __le__(self, other: Self) -> bool:
        return self.position <= other.position

    def __gt__(self, other: Self) -> bool:
        return self.position > other.position

    def __ge__(self, other: Self) -> bool:
        return self.position >= other.position

    @override
    def __hash__(self):
        return object.__hash__(self)


@dataclass(frozen=True, slots=True)
class RulesetCustomFields:
    """
    Base class for race format fields
    """


class SafeRaceFormat[T: RulesetCustomFields](NamedTuple):
    """
    Immutable for holding race format data
    """

    stage_time_sec: int
    random_stage_delay: int
    unlimited_time: bool
    race_time_sec: int
    overtime_sec: int
    fields: T

    @classmethod
    def from_format(cls, format_: RaceFormat) -> Self:
        """
        Builds an immutable from the a database race format instance and
        the ruleset fields default values.

        This classmethod checks current database values against the current
        definition of the format's custom fields. This prevent issues in the
        event fields saved in the database no longer reflect the defined field(s)
        """
        ruleset: RaceRuleset[T, Any] = RaceRulesetManager.get_ruleset(  # pyright: ignore[reportAssignmentType]
            format_.ruleset_id
        )
        fmt_fields = ruleset.__meta__.fields
        keys_types = {field.name: field.type for field in fields(fmt_fields)}

        fields_ = {
            field.name: field.value
            for field in format_.ruleset_fields
            if field.name in keys_types
            and isinstance(type_ := keys_types[field.name], type)
            and isinstance(field.value, type_)
        }

        return cls(
            format_.stage_time_sec,
            format_.random_stage_delay,
            format_.unlimited_time,
            format_.race_time_sec,
            format_.overtime_sec,
            fmt_fields(**fields_),
        )


class RulesetMeta[T: RulesetCustomFields](NamedTuple):
    """
    Ruleset metadata
    """

    uid: str
    """ruleset unique identifier"""
    fields: type[T]
    """custom fields for ruleset"""


class RaceRuleset[T: RulesetCustomFields, U: Any](ABC):
    """
    Abstract base class for processing race data.
    Can be used to enforce custom rulesets
    """

    __meta__: RulesetMeta[T]

    @abstractmethod
    def __init__(self, race_format: SafeRaceFormat[T]) -> None:
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
    def get_race_results(self) -> Sequence[SlotResult[U]]:
        """
        Get the results of the race

        :return: An iterable of the results for all the slots
        """

    @abstractmethod
    def get_slot_result(self, slot_num: int) -> SlotResult[U] | None:
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

            uid = ruleset_class.__meta__.uid  # pyright: ignore[reportGeneralTypeIssues]
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
    def _clear_registered(cls) -> None:
        """
        UNIT TESTING ONLY: Clears all registered rulesets.
        """
        cls._registered_ruleset.clear()


def register_ruleset(interface_class: type[RaceRuleset]) -> type[RaceRuleset]:
    """
    Decorator used for registering :py:class:`~pulsarity.api.ruleset.RaceRuleset`
    classes when its module is imported.

    :param interface_class: The race ruleset class to register
    :return: The registered race ruleset
    """
    return RaceRulesetManager.register(interface_class)
