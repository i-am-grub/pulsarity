"""Event Abstractions."""

import itertools
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, unique
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Self, dataclass_transform
from uuid import UUID

from pulsarity._core._protobuf.websocket_pb2 import (
    EventID,
    WebsocketEvent,
)

if TYPE_CHECKING:
    from pulsarity._core.database.permission import UserPermission

server_evt_registry: set[EventID] = set()
client_evt_registry: dict[EventID, type[ClientEventData]] = {}


@unique
class EvtPriority(Enum):
    """The priority of the event over other events that may be queued."""

    HIGHEST = 1
    HIGHER = 2
    HIGH = 3
    MEDIUM = 4
    LOW = 5
    LOWER = 6
    LOWEST = 7

    def __lt__(self, other: Self):
        return self.value < other.value


@dataclass_transform(frozen_default=True)
def server_event[T: ServerEventData](cls: type[T]) -> type[T]:
    """Decorator for generating registering system event handlers as dataclasses."""
    if cls.event_id in server_evt_registry:
        msg = f"Class with event_id={cls.event_id} already registered"
        raise ValueError(msg)

    if issubclass(cls, ServerEventData):
        server_evt_registry.add(cls.event_id)
        return dataclass(cls, frozen=True, slots=True)

    msg = f"{cls.__name__} is not a subclass of {ServerEventData.__name__}"
    raise TypeError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerEventData(ABC):
    """ABC for event data originating on the server."""

    _counter: ClassVar = itertools.count()
    """Event data ID generator"""

    event_id: ClassVar[EventID]
    """Protocol buffer event id"""
    priority: ClassVar[EvtPriority]
    """Outgoing priority"""
    permission: ClassVar[UserPermission]
    """Outgoing required client permission"""

    _id: int = field(default_factory=partial(next, _counter), init=False)
    """ID of the event data"""
    uuid: uuid.UUID = field(default_factory=uuid.uuid4)
    """Unique instance identifier"""
    _cached_message: bytes | None = field(default=None, init=False)
    """Serialized message cache"""

    def serialize_message(self) -> bytes:
        """Generate a serialized message from the server event."""
        return WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
        ).SerializeToString()

    def message_dump_protobuf(self) -> bytes:
        """Serialize as a protocol buffer message.

        This method will cache a serialized method in the event it is
        distributed to more than one client.
        """
        if self._cached_message is None:
            serialized_message = self.serialize_message()
            object.__setattr__(self, "_cached_message", serialized_message)
        return self._cached_message  # pyright: ignore[reportReturnType]

    def __lt__(self, other: Self) -> bool:
        return (self.priority, self._id) < (other.priority, other._id)


@dataclass_transform(frozen_default=True)
def client_event[T: ClientEventData](cls: type[T]) -> type[T]:
    """Decorator for generating registering client event handlers as dataclasses."""
    if cls.event_id in client_evt_registry:
        msg = f"Class with event_id={cls.event_id} already used"
        raise ValueError(msg)

    if issubclass(cls, ClientEventData):
        data_cls = dataclass(cls, frozen=True, slots=True)
        client_evt_registry[cls.event_id] = data_cls
        return data_cls

    msg = f"{cls.__name__} is not a subclass of {ClientEventData.__name__}"
    raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ClientEventData(ABC):
    """ABC for event data originating on the client."""

    event_id: ClassVar[EventID]
    """Protocol buffer event id"""
    permission: ClassVar[UserPermission]
    """Incoming required client permission"""

    uuid: UUID
    """Unique identifier"""

    @classmethod
    @abstractmethod
    def from_ws_event(cls, msg: WebsocketEvent) -> Self:
        """Parse event from websocket data.

        Any additiional validation for the parsed data should run here.
        It is safe to raise TypeError or ValueError in non-abstract implementations.
        """

    @abstractmethod
    async def process(self):
        """Process the client event."""
