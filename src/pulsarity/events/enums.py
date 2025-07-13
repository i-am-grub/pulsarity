"""
Enums for system events
"""

from dataclasses import dataclass
from enum import Enum, IntEnum, auto

from pulsarity.database.permission import SystemDefaultPerms, UserPermission


class EvtPriority(IntEnum):
    """
    The priority of the event over other events that may
    be queued. By default, this is does not determine the
    execution order of tasks in the event loop, but
    addtional logic can be combined to create an instant
    action.
    """

    HIGHEST = auto()
    HIGHER = auto()
    HIGH = auto()
    MEDUIUM = auto()
    LOW = auto()
    LOWER = auto()
    LOWEST = auto()


@dataclass
class _EvtData:
    """
    The dataclass used to define event enums
    """

    priority: EvtPriority
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
    def _generate_next_value_(name: str, *_):
        """
        Return the lower-cased version of the member name. Follows
        the method defined for StrEnum in the standard library
        """
        return name.lower()


class SpecialEvt(_ApplicationEvt):
    """
    Special Events
    """

    HEARTBEAT = EvtPriority.LOW, SystemDefaultPerms.EVENT_WEBSOCKET, auto()
    PERMISSIONS_UPDATE = EvtPriority.HIGH, SystemDefaultPerms.EVENT_WEBSOCKET, auto()
    STARTUP = EvtPriority.HIGHEST, SystemDefaultPerms.EVENT_WEBSOCKET, auto()
    SHUTDOWN = EvtPriority.HIGHEST, SystemDefaultPerms.EVENT_WEBSOCKET, auto()
    RESTART = EvtPriority.LOW, SystemDefaultPerms.SYSTEM_CONTROL, auto()


class EventSetupEvt(_ApplicationEvt):
    """
    Events associated with modification to race objects
    """

    PILOT_ADD = EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()
    PILOT_ALTER = EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()
    PILOT_DELETE = EvtPriority.MEDUIUM, SystemDefaultPerms.READ_PILOTS, auto()


class RaceSequenceEvt(_ApplicationEvt):
    """
    Events associated with live race sequence
    """

    RACE_SCHEDULE = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_STAGE = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_START = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_FINISH = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_STOP = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_PAUSE = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
    RACE_RESUME = EvtPriority.HIGHEST, SystemDefaultPerms.RACE_EVENTS, auto()
