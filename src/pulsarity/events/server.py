"""
System events originating on the server
"""

import functools
import itertools
import uuid as _uuid
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import ClassVar, Self, dataclass_transform, override
from uuid import UUID

from pulsarity._protobuf import websocket_pb2
from pulsarity.database.permission import SystemDefaultPerms, UserPermission

_registered: set[websocket_pb2.EventID] = set()


@dataclass_transform(frozen_default=True)
def system_event(cls: type[SystemEventData]) -> type[SystemEventData]:
    """
    Decorator for generating registering system event handlers as dataclasses
    """
    if cls.event_id in _registered:
        msg = f"Class with event_id={cls.event_id} already used"
        raise ValueError(msg)

    if issubclass(cls, SystemEventData):
        _registered.add(cls.event_id)
        return dataclass(cls, frozen=True)

    msg = f"{cls.__name__} is not a subclass of {SystemEventData.__name__}"
    raise TypeError(msg)


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


@dataclass(frozen=True, kw_only=True)
class SystemEventData(ABC):
    """
    ABC for event data originating on the server
    """

    event_id: ClassVar[websocket_pb2.EventID]
    """Protocol buffer event id"""
    priority: ClassVar[EvtPriority]
    """Outgoing priority"""
    permission: ClassVar[UserPermission]
    """Outgoing required client permission"""

    _counter: ClassVar[itertools.count] = itertools.count()
    _id: int = field(default_factory=functools.partial(next, _counter))

    uuid: UUID = field(default_factory=_uuid.uuid4)
    """Unique instance identifier"""

    @functools.cached_property
    def dumped_model(self) -> bytes:
        """
        Cached serialized message
        """
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes, event_id=self.event_id
        ).SerializeToString()

    def model_dump_protobuf(self) -> bytes:
        """
        Serialize as a protocol buffer message
        """
        return self.dumped_model

    def __lt__(self, other: Self) -> bool:
        return (self.priority, self._id) < (other.priority, other._id)


@system_event
class SystemHeartBeatEcho(SystemEventData):
    """
    Heartbeat echo
    """

    event_id = websocket_pb2.EVENT_HEARTBEAT
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class SystemPermissionUpdate(SystemEventData):
    """
    Permission update
    """

    event_id = websocket_pb2.EVENT_PERMISSIONS_UPDATE
    priority = EvtPriority.HIGH
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class ServerStartup(SystemEventData):
    """
    System startup event
    """

    event_id = websocket_pb2.EVENT_STARTUP
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class ServerShutdown(SystemEventData):
    """
    System shutdown event
    """

    event_id = websocket_pb2.EVENT_SHUTDOWN
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class ServerRestart(SystemEventData):
    """
    System restart event
    """

    event_id = websocket_pb2.EVENT_RESTART
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceSchedule(SystemEventData):
    """
    Race schedule event
    """

    event_id = websocket_pb2.EVENT_RACE_SCHEDULE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceStage(SystemEventData):
    """
    Race stage event
    """

    event_id = websocket_pb2.EVENT_RACE_STAGE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceStart(SystemEventData):
    """
    Race schedule event
    """

    event_id = websocket_pb2.EVENT_RACE_START
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceFinish(SystemEventData):
    """
    Race stop event
    """

    event_id = websocket_pb2.EVENT_RACE_FINISH
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceStop(SystemEventData):
    """
    Race stop event
    """

    event_id = websocket_pb2.EVENT_RACE_STOP
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RacePause(SystemEventData):
    """
    Race stop event
    """

    event_id = websocket_pb2.EVENT_RACE_PAUSE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class RaceResume(SystemEventData):
    """
    Race stop event
    """

    event_id = websocket_pb2.EVENT_RACE_RESUME
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class PilotAdd(SystemEventData):
    """
    Pilot Add event
    """

    event_id: ClassVar[websocket_pb2.EventID] = websocket_pb2.EVENT_PILOT_ADD
    priority = EvtPriority.MEDUIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    @functools.cached_property
    def dumped_model(self) -> bytes:
        pilot_data = websocket_pb2.PilotAddData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_add=pilot_data,
        ).SerializeToString()


@system_event
class PilotAlter(SystemEventData):
    """
    Pilot alter event
    """

    event_id: ClassVar[websocket_pb2.EventID] = websocket_pb2.EVENT_PILOT_ALTER
    priority = EvtPriority.MEDUIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    @functools.cached_property
    def dumped_model(self) -> bytes:
        pilot_data = websocket_pb2.PilotAlterData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_alter=pilot_data,
        ).SerializeToString()


@system_event
class PilotDelete(SystemEventData):
    """
    Pilot delete event
    """

    event_id = websocket_pb2.EVENT_PILOT_DELETE
    priority = EvtPriority.MEDUIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    @functools.cached_property
    def dumped_model(self) -> bytes:
        pilot_data = websocket_pb2.PilotDeleteData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_delete=pilot_data,
        ).SerializeToString()
