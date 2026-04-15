"""
System event handler registry
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Self, TypeVar, dataclass_transform, override
from uuid import UUID

from pulsarity import ctx
from pulsarity._protobuf import websocket_pb2
from pulsarity.events.enums import SystemEvt

# pylint: disable=E1121

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class _WSEvent(ABC):
    evt: ClassVar[SystemEvt]
    uuid: UUID

    @classmethod
    @abstractmethod
    def from_ws_event(cls, msg: websocket_pb2.WebsocketEvent) -> Self:
        """
        Get route from websocket event
        """

    @abstractmethod
    async def client_trigger(self):
        """
        Run the route's functionality
        """

    def model_dump_protobuf(self) -> bytes:
        """
        Serialize as a protocol buffer message
        """
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes, event_id=self.evt.event_id
        ).SerializeToString()


registry: dict[websocket_pb2.EventID, type[_WSEvent]] = {}


@dataclass_transform(frozen_default=True)
def event_handler(cls: type[_WSEvent]) -> type[_WSEvent]:
    """
    Decorator for generating dataclasses and registering event handlers
    """

    if cls.evt.event_id in registry:
        msg = f"Class with value {cls.evt.event_id} already used"
        raise ValueError(msg)

    if issubclass(cls, _WSEvent):
        data_cls = dataclass(cls, frozen=True, slots=True)
        registry[cls.evt.event_id] = data_cls
        return data_cls

    msg = f"{cls.__name__} is not a subclass of {_WSEvent.__name__}"
    raise TypeError(msg)


@event_handler
class HeartBeatEcho(_WSEvent):
    """
    Heartbeat echo event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.HEARTBEAT

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def client_trigger(self):
        event_broker = ctx.event_broker_ctx.get()
        event_broker.publish(SystemEvt.HEARTBEAT, uuid_=self.uuid)


@event_handler
class ServerShutdown(_WSEvent):
    """
    System shutdown event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.SHUTDOWN
    shutdown_evt: ClassVar[asyncio.Event] = asyncio.Event()

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def client_trigger(self):
        self.shutdown_evt.set()


@event_handler
class ServerRestart(_WSEvent):
    """
    System restart event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.RESTART
    restart_evt: ClassVar[asyncio.Event] = asyncio.Event()

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def client_trigger(self):
        self.restart_evt.set()


@event_handler
class ScheduleRace(_WSEvent):
    """
    Race schedule event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.RACE_SCHEDULE

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def client_trigger(self): ...


@event_handler
class StopRace(_WSEvent):
    """
    Race stop event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.RACE_STOP

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def client_trigger(self):
        ctx.race_manager_ctx.get().stop_race()


@event_handler
class PilotAdd(_WSEvent):
    """
    Pilot Add event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.PILOT_ADD
    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_add.pilot_id)

    async def client_trigger(self): ...

    @override
    def model_dump_protobuf(self) -> bytes:
        pilot_data = websocket_pb2.PilotAddData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.evt.event_id,
            pilot_add=pilot_data,
        ).SerializeToString()


@event_handler
class PilotAlter(_WSEvent):
    """
    Pilot alter event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.PILOT_ALTER
    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_alter.pilot_id)

    async def client_trigger(self): ...

    @override
    def model_dump_protobuf(self) -> bytes:
        pilot_data = websocket_pb2.PilotAlterData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.evt.event_id,
            pilot_alter=pilot_data,
        ).SerializeToString()


@event_handler
class PilotDelete(_WSEvent):
    """
    Pilot delete event
    """

    evt: ClassVar[SystemEvt] = SystemEvt.PILOT_DELETE
    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_delete.pilot_id)

    async def client_trigger(self): ...

    @override
    def model_dump_protobuf(self) -> bytes:
        pilot_data = websocket_pb2.PilotDeleteData(pilot_id=self.pilot_id)
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.evt.event_id,
            pilot_delete=pilot_data,
        ).SerializeToString()
