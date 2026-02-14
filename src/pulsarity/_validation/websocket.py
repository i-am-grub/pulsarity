from typing import Annotated, Literal, Union

from pydantic import UUID4, BaseModel, ConfigDict, Field

from pulsarity._protobuf import websocket_pb2


class BaseEvent(BaseModel):
    """
    Base model for validating incoming and outgoing
    websocket data
    """

    model_config = ConfigDict(frozen=True)

    uuid: UUID4
    event_id: Literal[websocket_pb2.EVENT_UNSPECIFIED]  # type: ignore

    def model_dump_protobuf(self) -> bytes:
        """
        Serialize as a protocol buffer message
        """

        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes, event_id=self.event_id
        ).SerializeToString()


class SystemHeartbeat(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_HEARTBEAT]  # type: ignore


class SystemShutdown(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_SHUTDOWN]  # type: ignore


class SystemRestart(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_RESTART]  # type: ignore


class ScheduleRace(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_RACE_SCHEDULE]  # type: ignore


class RaceStop(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_RACE_STOP]  # type: ignore


class PilotAddData(BaseModel):
    pilot_id: int


class PilotAddEvent(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_PILOT_ADD]  # type: ignore
    pilot_add: PilotAddData

    def model_dump_protobuf(self) -> bytes:
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_add=self.pilot_add.model_dump(),
        ).SerializeToString()


class PilotAlterData(BaseModel):
    pilot_id: int


class PilotAlterEvent(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_PILOT_ALTER]  # type: ignore
    pilot_alter: PilotAlterData

    def model_dump_protobuf(self) -> bytes:
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_alter=self.pilot_alter.model_dump(),
        ).SerializeToString()


class PilotDeleteData(BaseModel):
    pilot_id: int


class PilotDeleteEvent(BaseEvent):
    event_id: Literal[websocket_pb2.EVENT_PILOT_DELETE]  # type: ignore
    pilot_delete: PilotDeleteData

    def model_dump_protobuf(self) -> bytes:
        return websocket_pb2.WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_delete=self.pilot_delete.model_dump(),
        ).SerializeToString()


WebsocketEvent = Annotated[
    Union[
        SystemHeartbeat,
        SystemShutdown,
        SystemRestart,
        ScheduleRace,
        RaceStop,
        PilotAddEvent,
        PilotAlterEvent,
        PilotDeleteEvent,
    ],
    Field(discriminator="event_id"),
]
