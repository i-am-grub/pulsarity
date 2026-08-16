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

class NumberFieldData(_message.Message):
    __slots__ = ["max", "min", "step", "value"]
    MAX_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    max: float
    min: float
    step: float
    value: float
    def __init__(self, value: _Optional[float] = ..., min: _Optional[float] = ..., max: _Optional[float] = ..., step: _Optional[float] = ...) -> None: ...

class SelectFieldData(_message.Message):
    __slots__ = ["mapping", "selected"]
    class MappingEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str
        def __init__(self, key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...
    MAPPING_FIELD_NUMBER: _ClassVar[int]
    SELECTED_FIELD_NUMBER: _ClassVar[int]
    mapping: _containers.ScalarMap[int, str]
    selected: int
    def __init__(self, mapping: _Optional[_Mapping[int, str]] = ..., selected: _Optional[int] = ...) -> None: ...

class UIButtonField(_message.Message):
    __slots__ = ["element_id", "hidden", "text"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    HIDDEN_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    hidden: bool
    text: str
    def __init__(self, element_id: _Optional[int] = ..., hidden: bool = ..., text: _Optional[str] = ...) -> None: ...

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
    __slots__ = ["element_id", "elements", "hidden"]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    HIDDEN_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    elements: _containers.RepeatedCompositeFieldContainer[UIElementTreeEntry]
    hidden: bool
    def __init__(self, element_id: _Optional[int] = ..., hidden: bool = ..., elements: _Optional[_Iterable[_Union[UIElementTreeEntry, _Mapping]]] = ...) -> None: ...

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
    __slots__ = ["button", "element_id", "element_type", "etree", "markdown", "value"]
    BUTTON_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    ETREE_FIELD_NUMBER: _ClassVar[int]
    MARKDOWN_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    button: UIButtonField
    element_id: int
    element_type: UIElementType
    etree: UIElementTree
    markdown: UIMarkdownField
    value: UIValueField
    def __init__(self, element_type: _Optional[_Union[UIElementType, str]] = ..., element_id: _Optional[int] = ..., etree: _Optional[_Union[UIElementTree, _Mapping]] = ..., markdown: _Optional[_Union[UIMarkdownField, _Mapping]] = ..., button: _Optional[_Union[UIButtonField, _Mapping]] = ..., value: _Optional[_Union[UIValueField, _Mapping]] = ...) -> None: ...

class UIMarkdownField(_message.Message):
    __slots__ = ["element_id", "hidden", "text"]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    HIDDEN_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    hidden: bool
    text: str
    def __init__(self, element_id: _Optional[int] = ..., hidden: bool = ..., text: _Optional[str] = ...) -> None: ...

class UIMarkdownFields(_message.Message):
    __slots__ = ["fields"]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIMarkdownField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIMarkdownField, _Mapping]]] = ...) -> None: ...

class UIValueField(_message.Message):
    __slots__ = ["boolean", "datetime", "description", "element_id", "field_type", "hidden", "number", "select", "text"]
    BOOLEAN_FIELD_NUMBER: _ClassVar[int]
    DATETIME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_TYPE_FIELD_NUMBER: _ClassVar[int]
    HIDDEN_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    SELECT_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    boolean: bool
    datetime: _timestamp_pb2.Timestamp
    description: str
    element_id: int
    field_type: FieldType
    hidden: bool
    number: NumberFieldData
    select: SelectFieldData
    text: str
    def __init__(self, element_id: _Optional[int] = ..., hidden: bool = ..., field_type: _Optional[_Union[FieldType, str]] = ..., description: _Optional[str] = ..., text: _Optional[str] = ..., number: _Optional[_Union[NumberFieldData, _Mapping]] = ..., boolean: bool = ..., datetime: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., select: _Optional[_Union[SelectFieldData, _Mapping]] = ...) -> None: ...

class UIValueFields(_message.Message):
    __slots__ = ["fields"]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIValueField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIValueField, _Mapping]]] = ...) -> None: ...

class UIElementType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class FieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
