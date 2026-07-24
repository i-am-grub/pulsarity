from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
ELEMENT_TYPE_BUTTON: UIElementType
ELEMENT_TYPE_ETREE: UIElementType
ELEMENT_TYPE_MARKDOWN: UIElementType
ELEMENT_TYPE_UNKNOWN: UIElementType
ELEMENT_TYPE_VALUE: UIElementType
FIELD_TYPE_BASIC_INT: FieldType
FIELD_TYPE_CHECKBOX: FieldType
FIELD_TYPE_DATE: FieldType
FIELD_TYPE_DATETIME: FieldType
FIELD_TYPE_EMAIL: FieldType
FIELD_TYPE_NUMBER: FieldType
FIELD_TYPE_PASSWORD: FieldType
FIELD_TYPE_RANGE: FieldType
FIELD_TYPE_SELECT: FieldType
FIELD_TYPE_TEL: FieldType
FIELD_TYPE_TEXT: FieldType
FIELD_TYPE_TIME: FieldType
FIELD_TYPE_UNKNOWN: FieldType
FIELD_TYPE_URL: FieldType

class MappedElementTrees(_message.Message):
    __slots__ = ["element_ids"]
    ELEMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    element_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, element_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class RangeData(_message.Message):
    __slots__ = ["max", "min", "scale", "value"]
    MAX_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    max: float
    min: float
    scale: float
    value: float
    def __init__(self, min: _Optional[float] = ..., max: _Optional[float] = ..., value: _Optional[float] = ..., scale: _Optional[float] = ...) -> None: ...

class UIButtonField(_message.Message):
    __slots__ = ["element_id", "text"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    text: str
    def __init__(self, element_id: _Optional[int] = ..., text: _Optional[str] = ...) -> None: ...

class UIButtonFields(_message.Message):
    __slots__ = ["fields"]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIButtonField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIButtonField, _Mapping]]] = ...) -> None: ...

class UIETreeMapping(_message.Message):
    __slots__ = ["mapping"]
    class MappingEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: MappedElementTrees
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[MappedElementTrees, _Mapping]] = ...) -> None: ...
    MAPPING_FIELD_NUMBER: _ClassVar[int]
    mapping: _containers.MessageMap[str, MappedElementTrees]
    def __init__(self, mapping: _Optional[_Mapping[str, MappedElementTrees]] = ...) -> None: ...

class UIElementTree(_message.Message):
    __slots__ = ["element_id", "elements"]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    elements: _containers.RepeatedCompositeFieldContainer[UIElementTreeEntry]
    def __init__(self, element_id: _Optional[int] = ..., elements: _Optional[_Iterable[_Union[UIElementTreeEntry, _Mapping]]] = ...) -> None: ...

class UIElementTreeEntry(_message.Message):
    __slots__ = ["element_id", "type"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    type: UIElementType
    def __init__(self, type: _Optional[_Union[UIElementType, str]] = ..., element_id: _Optional[int] = ...) -> None: ...

class UIElementTrees(_message.Message):
    __slots__ = ["etrees"]
    ETREES_FIELD_NUMBER: _ClassVar[int]
    etrees: _containers.RepeatedCompositeFieldContainer[UIElementTree]
    def __init__(self, etrees: _Optional[_Iterable[_Union[UIElementTree, _Mapping]]] = ...) -> None: ...

class UIElementUpdate(_message.Message):
    __slots__ = ["element_id", "element_type", "etree"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    ETREE_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    element_type: UIElementType
    etree: UIElementTree
    def __init__(self, element_type: _Optional[_Union[UIElementType, str]] = ..., element_id: _Optional[int] = ..., etree: _Optional[_Union[UIElementTree, _Mapping]] = ...) -> None: ...

class UIMarkdownField(_message.Message):
    __slots__ = ["element_id", "text"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    text: str
    def __init__(self, element_id: _Optional[int] = ..., text: _Optional[str] = ...) -> None: ...

class UIMarkdownFields(_message.Message):
    __slots__ = ["fields"]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIMarkdownField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIMarkdownField, _Mapping]]] = ...) -> None: ...

class UIValueField(_message.Message):
    __slots__ = ["boolean", "datetime", "decimal", "element_id", "field_type", "integar", "range", "text"]
    BOOLEAN_FIELD_NUMBER: _ClassVar[int]
    DATETIME_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_TYPE_FIELD_NUMBER: _ClassVar[int]
    INTEGAR_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    boolean: bool
    datetime: _timestamp_pb2.Timestamp
    decimal: float
    element_id: int
    field_type: FieldType
    integar: int
    range: RangeData
    text: str
    def __init__(self, element_id: _Optional[int] = ..., field_type: _Optional[_Union[FieldType, str]] = ..., text: _Optional[str] = ..., boolean: bool = ..., integar: _Optional[int] = ..., decimal: _Optional[float] = ..., datetime: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., range: _Optional[_Union[RangeData, _Mapping]] = ...) -> None: ...

class UIValueFields(_message.Message):
    __slots__ = ["fields"]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIValueField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIValueField, _Mapping]]] = ...) -> None: ...

class UIElementType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class FieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
