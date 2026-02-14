"""
Enums for system events
"""

from dataclasses import dataclass
from enum import Enum, IntEnum, auto

from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.protobuf import websocket_pb2


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


@dataclass(frozen=True)
class _EvtData:
    """
    The dataclass used to define event enums
    """

    priority: EvtPriority
    """The priority associated with the event"""
    permission: UserPermission
    """The permission the event is associated with"""
    event_id: websocket_pb2.EventID
    """Identifier for the event. This field should match the protocol buffer value"""


class _ApplicationEvt(_EvtData, Enum):
    """
    Parent enum for system events. Primarily
    used for typing.
    """


class SpecialEvt(_ApplicationEvt):
    """
    Special Events
    """

    HEARTBEAT = (
        EvtPriority.LOW,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_HEARTBEAT,
    )
    PERMISSIONS_UPDATE = (
        EvtPriority.HIGH,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_PERMISSIONS_UPDATE,
    )
    STARTUP = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_STARTUP,
    )
    SHUTDOWN = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_SHUTDOWN,
    )
    RESTART = (
        EvtPriority.LOW,
        SystemDefaultPerms.SYSTEM_CONTROL,
        websocket_pb2.EVENT_RESTART,
    )


class EventSetupEvt(_ApplicationEvt):
    """
    Events associated with modification to race objects
    """

    PILOT_ADD = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_ADD,
    )
    PILOT_ALTER = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_ALTER,
    )
    PILOT_DELETE = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_DELETE,
    )


class RaceSequenceEvt(_ApplicationEvt):
    """
    Events associated with live race sequence
    """

    RACE_SCHEDULE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_SCHEDULE,
    )
    RACE_STAGE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_STAGE,
    )
    RACE_START = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_START,
    )
    RACE_FINISH = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_FINISH,
    )
    RACE_STOP = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_STOP,
    )
    RACE_PAUSE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_PAUSE,
    )
    RACE_RESUME = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_RESUME,
    )
