"""
Enums for system events
"""

from dataclasses import dataclass
from enum import Enum, unique
from typing import Self

from pulsarity._protobuf import websocket_pb2
from pulsarity.database.permission import SystemDefaultPerms, UserPermission


@unique
class EvtPriority(Enum):
    """
    The priority of the event over other events that may
    be queued. By default, this is does not determine the
    execution order of tasks in the event loop, but
    addtional logic can be combined to create an instant
    action.
    """

    HIGHEST = 1
    HIGHER = 2
    HIGH = 3
    MEDUIUM = 4
    LOW = 5
    LOWER = 6
    LOWEST = 7

    def __lt__(self, other: Self):
        return self.value < other.value


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


@unique
class SystemEvt(_EvtData, Enum):
    """
    System events
    """

    # Special Events
    HEARTBEAT = (
        EvtPriority.LOW,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_HEARTBEAT,
    )
    """Webserver heartbeat event"""
    PERMISSIONS_UPDATE = (
        EvtPriority.HIGH,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_PERMISSIONS_UPDATE,
    )
    """User permission update event"""
    STARTUP = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_STARTUP,
    )
    """System startup event"""
    SHUTDOWN = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.EVENT_WEBSOCKET,
        websocket_pb2.EVENT_SHUTDOWN,
    )
    """System shutdown event"""
    RESTART = (
        EvtPriority.LOW,
        SystemDefaultPerms.SYSTEM_CONTROL,
        websocket_pb2.EVENT_RESTART,
    )
    """System restart event"""

    # Events associated with modification to race objects
    PILOT_ADD = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_ADD,
    )
    """Pilot add event"""
    PILOT_ALTER = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_ALTER,
    )
    """Pilot alter event"""
    PILOT_DELETE = (
        EvtPriority.MEDUIUM,
        SystemDefaultPerms.READ_PILOTS,
        websocket_pb2.EVENT_PILOT_DELETE,
    )
    """Pilot delete event"""

    # Events associated with live race sequence
    RACE_SCHEDULE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_SCHEDULE,
    )
    """Race scheduled event"""
    RACE_STAGE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_STAGE,
    )
    """Race stage event"""
    RACE_START = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_START,
    )
    """Race start event"""
    RACE_FINISH = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_FINISH,
    )
    """Race finish event"""
    RACE_STOP = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_STOP,
    )
    """Race stop event"""
    RACE_PAUSE = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_PAUSE,
    )
    """Race pause event"""
    RACE_RESUME = (
        EvtPriority.HIGHEST,
        SystemDefaultPerms.RACE_CONTROL,
        websocket_pb2.EVENT_RACE_RESUME,
    )
    """Race resume event"""
