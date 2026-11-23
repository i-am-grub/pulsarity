import pulsarity._core._protobuf.ui_pb2 as _ui_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventID(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_UNSPECIFIED: _ClassVar[EventID]
    EVENT_HEARTBEAT: _ClassVar[EventID]
    EVENT_PERMISSIONS_UPDATE: _ClassVar[EventID]
    EVENT_STARTUP: _ClassVar[EventID]
    EVENT_SHUTDOWN: _ClassVar[EventID]
    EVENT_RESTART: _ClassVar[EventID]
    EVENT_UI_UPDATE: _ClassVar[EventID]
    EVENT_RACE_SCHEDULE: _ClassVar[EventID]
    EVENT_RACE_STAGE: _ClassVar[EventID]
    EVENT_RACE_START: _ClassVar[EventID]
    EVENT_RACE_FINISH: _ClassVar[EventID]
    EVENT_RACE_STOP: _ClassVar[EventID]
    EVENT_RACE_PAUSE: _ClassVar[EventID]
    EVENT_RACE_RESUME: _ClassVar[EventID]
    EVENT_PILOT_ADD: _ClassVar[EventID]
    EVENT_PILOT_ALTER: _ClassVar[EventID]
    EVENT_PILOT_DELETE: _ClassVar[EventID]
EVENT_UNSPECIFIED: EventID
EVENT_HEARTBEAT: EventID
EVENT_PERMISSIONS_UPDATE: EventID
EVENT_STARTUP: EventID
EVENT_SHUTDOWN: EventID
EVENT_RESTART: EventID
EVENT_UI_UPDATE: EventID
EVENT_RACE_SCHEDULE: EventID
EVENT_RACE_STAGE: EventID
EVENT_RACE_START: EventID
EVENT_RACE_FINISH: EventID
EVENT_RACE_STOP: EventID
EVENT_RACE_PAUSE: EventID
EVENT_RACE_RESUME: EventID
EVENT_PILOT_ADD: EventID
EVENT_PILOT_ALTER: EventID
EVENT_PILOT_DELETE: EventID

class PilotAddData(_message.Message):
    __slots__ = ("pilot_id",)
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class PilotAlterData(_message.Message):
    __slots__ = ("pilot_id",)
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class PilotDeleteData(_message.Message):
    __slots__ = ("pilot_id",)
    PILOT_ID_FIELD_NUMBER: _ClassVar[int]
    pilot_id: int
    def __init__(self, pilot_id: _Optional[int] = ...) -> None: ...

class WebsocketEvent(_message.Message):
    __slots__ = ("uuid", "event_id", "ui_element_update", "pilot_add", "pilot_alter", "pilot_delete")
    UUID_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    UI_ELEMENT_UPDATE_FIELD_NUMBER: _ClassVar[int]
    PILOT_ADD_FIELD_NUMBER: _ClassVar[int]
    PILOT_ALTER_FIELD_NUMBER: _ClassVar[int]
    PILOT_DELETE_FIELD_NUMBER: _ClassVar[int]
    uuid: bytes
    event_id: EventID
    ui_element_update: _ui_pb2.UIElementUpdate
    pilot_add: PilotAddData
    pilot_alter: PilotAlterData
    pilot_delete: PilotDeleteData
    def __init__(self, uuid: _Optional[bytes] = ..., event_id: _Optional[_Union[EventID, str]] = ..., ui_element_update: _Optional[_Union[_ui_pb2.UIElementUpdate, _Mapping]] = ..., pilot_add: _Optional[_Union[PilotAddData, _Mapping]] = ..., pilot_alter: _Optional[_Union[PilotAlterData, _Mapping]] = ..., pilot_delete: _Optional[_Union[PilotDeleteData, _Mapping]] = ...) -> None: ...
