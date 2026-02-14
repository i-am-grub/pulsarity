from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
EVENT_HEARTBEAT: EventID
EVENT_PERMISSIONS_UPDATE: EventID
EVENT_PILOT_ADD: EventID
EVENT_PILOT_ALTER: EventID
EVENT_PILOT_DELETE: EventID
EVENT_RACE_FINISH: EventID
EVENT_RACE_PAUSE: EventID
EVENT_RACE_RESUME: EventID
EVENT_RACE_SCHEDULE: EventID
EVENT_RACE_STAGE: EventID
EVENT_RACE_START: EventID
EVENT_RACE_STOP: EventID
EVENT_RESTART: EventID
EVENT_SHUTDOWN: EventID
EVENT_STARTUP: EventID
EVENT_UNSPECIFIED: EventID

class PilotAddData(_message.Message):
    __slots__ = ["pilot_id"]
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class PilotAlterData(_message.Message):
    __slots__ = ["pilot_id"]
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class PilotDeleteData(_message.Message):
    __slots__ = ["pilot_id"]
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class WebsocketEvent(_message.Message):
    __slots__ = ["event_id", "pilot_add", "pilot_alter", "pilot_delete", "uuid"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    PILOT_ADD_FIELD_NUMBER: _ClassVar[int]
    PILOT_ALTER_FIELD_NUMBER: _ClassVar[int]
    PILOT_DELETE_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    event_id: EventID
    pilot_add: PilotAddData
    pilot_alter: PilotAlterData
    pilot_delete: PilotDeleteData
    uuid: bytes
    def __init__(self, uuid: _Optional[bytes] = ..., event_id: _Optional[_Union[EventID, str]] = ..., pilot_add: _Optional[_Union[PilotAddData, _Mapping]] = ..., pilot_alter: _Optional[_Union[PilotAlterData, _Mapping]] = ..., pilot_delete: _Optional[_Union[PilotDeleteData, _Mapping]] = ...) -> None: ...

class EventID(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
