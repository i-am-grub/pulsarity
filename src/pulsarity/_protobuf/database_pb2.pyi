from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Attribute(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Heat(_message.Message):
    __slots__ = ["attributes", "heat_num", "id"]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    HEAT_NUM_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedCompositeFieldContainer[Attribute]
    heat_num: int
    id: int
    def __init__(self, id: _Optional[int] = ..., heat_num: _Optional[int] = ..., attributes: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Heats(_message.Message):
    __slots__ = ["heats"]
    HEATS_FIELD_NUMBER: _ClassVar[int]
    heats: _containers.RepeatedCompositeFieldContainer[Heat]
    def __init__(self, heats: _Optional[_Iterable[_Union[Heat, _Mapping]]] = ...) -> None: ...

class Pilot(_message.Message):
    __slots__ = ["attributes", "display_callsign", "display_name", "id"]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_CALLSIGN_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedCompositeFieldContainer[Attribute]
    display_callsign: str
    display_name: str
    id: int
    def __init__(self, id: _Optional[int] = ..., display_callsign: _Optional[str] = ..., display_name: _Optional[str] = ..., attributes: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Pilots(_message.Message):
    __slots__ = ["pilots"]
    PILOTS_FIELD_NUMBER: _ClassVar[int]
    pilots: _containers.RepeatedCompositeFieldContainer[Pilot]
    def __init__(self, pilots: _Optional[_Iterable[_Union[Pilot, _Mapping]]] = ...) -> None: ...

class RaceClass(_message.Message):
    __slots__ = ["attributes", "id", "name"]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedCompositeFieldContainer[Attribute]
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., attributes: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class RaceClasses(_message.Message):
    __slots__ = ["raceclasses"]
    RACECLASSES_FIELD_NUMBER: _ClassVar[int]
    raceclasses: _containers.RepeatedCompositeFieldContainer[RaceClass]
    def __init__(self, raceclasses: _Optional[_Iterable[_Union[RaceClass, _Mapping]]] = ...) -> None: ...

class RaceEvent(_message.Message):
    __slots__ = ["attributes", "date", "id", "name"]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedCompositeFieldContainer[Attribute]
    date: _timestamp_pb2.Timestamp
    id: int
    name: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., attributes: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class RaceEvents(_message.Message):
    __slots__ = ["events"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[RaceEvent]
    def __init__(self, events: _Optional[_Iterable[_Union[RaceEvent, _Mapping]]] = ...) -> None: ...

class Round(_message.Message):
    __slots__ = ["attributes", "id", "round_num"]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ROUND_NUM_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedCompositeFieldContainer[Attribute]
    id: int
    round_num: int
    def __init__(self, id: _Optional[int] = ..., round_num: _Optional[int] = ..., attributes: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Rounds(_message.Message):
    __slots__ = ["rounds"]
    ROUNDS_FIELD_NUMBER: _ClassVar[int]
    rounds: _containers.RepeatedCompositeFieldContainer[Round]
    def __init__(self, rounds: _Optional[_Iterable[_Union[Round, _Mapping]]] = ...) -> None: ...
