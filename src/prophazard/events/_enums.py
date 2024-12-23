"""
Enums for system events
"""

from dataclasses import dataclass
from enum import IntEnum, Enum, auto

from ..database.user import UserPermission, SystemDefaultPerms


class _EvtPriority(IntEnum):
    """
    The priority of the event over other events that may
    be queued. By default, this is does not determine the
    execution order of tasks in the event loop, but
    addtional logic can be combined to create an instant
    action.
    """

    INSTANT = 1
    HIGH = 2
    MEDUIUM = 3
    LOW = 4


@dataclass
class _EvtData:
    """
    The dataclass used to define event enums
    """

    priority: _EvtPriority
    """The priority associated with the event"""
    permission: UserPermission
    """The permission the event is associated with"""
    id: str
    """Identifier for the event"""


class _ApplicationEvt(_EvtData, Enum):
    """
    Parent enum for system events. Primarily
    used for typing.
    """

    @staticmethod
    def _generate_next_value_(name: str, _start: int, _count: int, _last_values: list):
        """
        Return the lower-cased version of the member name. Follows
        the method defined for StrEnum in the standard library
        """
        return name.lower()


class EventSetupEvt(_ApplicationEvt):
    """
    Events associated with modification to race objects
    """

    PILOT_ADD = _EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()
    PILOT_ALTER = _EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()
    PILOT_DELETE = _EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()


class RaceSequenceEvt(_ApplicationEvt):
    """
    Events associated with live race sequence
    """

    RACE_STAGE = _EvtPriority.HIGH, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_START = _EvtPriority.INSTANT, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_FINISH = _EvtPriority.HIGH, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_STOP = _EvtPriority.INSTANT, SystemDefaultPerms.RACE_EVENTS, auto()
