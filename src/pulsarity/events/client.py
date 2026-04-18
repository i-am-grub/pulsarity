"""
System events originating on a client
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Self, dataclass_transform
from uuid import UUID

from pulsarity import ctx
from pulsarity._protobuf import websocket_pb2
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.events.server import SystemHeartBeatEcho

# pylint: disable=E1121

registry: dict[websocket_pb2.EventID, type[ClientEventData]] = {}


@dataclass_transform(frozen_default=True)
def client_event(cls: type[ClientEventData]) -> type[ClientEventData]:
    """
    Decorator for generating registering client event handlers as dataclasses
    """

    if cls.event_id in registry:
        msg = f"Class with event_id={cls.event_id} already used"
        raise ValueError(msg)

    if issubclass(cls, ClientEventData):
        data_cls = dataclass(cls, frozen=True, slots=True)
        registry[cls.event_id] = data_cls
        return data_cls

    msg = f"{cls.__name__} is not a subclass of {ClientEventData.__name__}"
    raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ClientEventData(ABC):
    """
    ABC for event data originating on the client
    """

    event_id: ClassVar[websocket_pb2.EventID]
    """Protocol buffer event id"""
    permission: ClassVar[UserPermission]
    """Incoming required client permission"""

    uuid: UUID
    """Unique identifier"""

    @classmethod
    @abstractmethod
    def from_ws_event(cls, msg: websocket_pb2.WebsocketEvent) -> Self:
        """
        Parse event from websocket data
        """

    @abstractmethod
    async def run_handler(self):
        """
        Run the handler's functionality
        """


@client_event
class ClientHeartbeat(ClientEventData):
    """
    Client heartbeat
    """

    event_id = websocket_pb2.EVENT_HEARTBEAT
    permission = SystemDefaultPerms.EVENT_WEBSOCKET

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def run_handler(self):
        websocket = ctx.websocket_ctx.get()
        response = SystemHeartBeatEcho(uuid=self.uuid).model_dump_protobuf()
        await websocket.send_bytes(response)


@client_event
class ClientServerShutdown(ClientEventData):
    """
    Client commanded system shutdown
    """

    event_id = websocket_pb2.EVENT_SHUTDOWN
    permission = SystemDefaultPerms.SYSTEM_CONTROL

    shutdown_evt: ClassVar[asyncio.Event] = asyncio.Event()

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def run_handler(self):
        self.shutdown_evt.set()


@client_event
class ClientServerRestart(ClientEventData):
    """
    Client commanded system restart
    """

    event_id = websocket_pb2.EVENT_RESTART
    permission = SystemDefaultPerms.SYSTEM_CONTROL

    restart_evt: ClassVar[asyncio.Event] = asyncio.Event()

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def run_handler(self):
        self.restart_evt.set()


@client_event
class ClientScheduleRace(ClientEventData):
    """
    Client commanded race schedule
    """

    event_id = websocket_pb2.EVENT_RACE_SCHEDULE
    permission = SystemDefaultPerms.RACE_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def run_handler(self):
        raise NotImplementedError


@client_event
class ClientStopRace(ClientEventData):
    """
    Client commanded race stop
    """

    event_id = websocket_pb2.EVENT_RACE_STOP
    permission = SystemDefaultPerms.RACE_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def run_handler(self):
        ctx.race_manager_ctx.get().stop_race()


@client_event
class ClientPilotAdd(ClientEventData):
    """
    Client commanded pilot add
    """

    event_id = websocket_pb2.EVENT_PILOT_ADD
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_add.pilot_id)

    async def run_handler(self):
        raise NotImplementedError


@client_event
class ClientPilotAlter(ClientEventData):
    """
    Client commanded pilot alter
    """

    event_id = websocket_pb2.EVENT_PILOT_ALTER
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_alter.pilot_id)

    async def run_handler(self):
        raise NotImplementedError


@client_event
class ClientPilotDelete(ClientEventData):
    """
    Client commanded pilot delete event
    """

    event_id = websocket_pb2.EVENT_PILOT_DELETE
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_delete.pilot_id)

    async def run_handler(self):
        raise NotImplementedError
