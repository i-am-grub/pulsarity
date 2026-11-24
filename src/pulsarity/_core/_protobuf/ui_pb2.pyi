import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UIElementType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ELEMENT_TYPE_UNKNOWN: _ClassVar[UIElementType]
    ELEMENT_TYPE_ETREE: _ClassVar[UIElementType]
    ELEMENT_TYPE_MARKDOWN: _ClassVar[UIElementType]
    ELEMENT_TYPE_BUTTON: _ClassVar[UIElementType]
    ELEMENT_TYPE_VALUE: _ClassVar[UIElementType]

class FieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FIELD_TYPE_UNKNOWN: _ClassVar[FieldType]
    FIELD_TYPE_TEXT: _ClassVar[FieldType]
    FIELD_TYPE_NUMBER: _ClassVar[FieldType]
    FIELD_TYPE_RANGE: _ClassVar[FieldType]
    FIELD_TYPE_SELECT: _ClassVar[FieldType]
    FIELD_TYPE_CHECKBOX: _ClassVar[FieldType]
    FIELD_TYPE_PASSWORD: _ClassVar[FieldType]
    FIELD_TYPE_DATETIME: _ClassVar[FieldType]
    FIELD_TYPE_DATE: _ClassVar[FieldType]
    FIELD_TYPE_TIME: _ClassVar[FieldType]
    FIELD_TYPE_EMAIL: _ClassVar[FieldType]
    FIELD_TYPE_TEL: _ClassVar[FieldType]
    FIELD_TYPE_URL: _ClassVar[FieldType]
ELEMENT_TYPE_UNKNOWN: UIElementType
ELEMENT_TYPE_ETREE: UIElementType
ELEMENT_TYPE_MARKDOWN: UIElementType
ELEMENT_TYPE_BUTTON: UIElementType
ELEMENT_TYPE_VALUE: UIElementType
FIELD_TYPE_UNKNOWN: FieldType
FIELD_TYPE_TEXT: FieldType
FIELD_TYPE_NUMBER: FieldType
FIELD_TYPE_RANGE: FieldType
FIELD_TYPE_SELECT: FieldType
FIELD_TYPE_CHECKBOX: FieldType
FIELD_TYPE_PASSWORD: FieldType
FIELD_TYPE_DATETIME: FieldType
FIELD_TYPE_DATE: FieldType
FIELD_TYPE_TIME: FieldType
FIELD_TYPE_EMAIL: FieldType
FIELD_TYPE_TEL: FieldType
FIELD_TYPE_URL: FieldType

class UIElementTreeEntry(_message.Message):
    __slots__ = ("type", "element_id")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    type: UIElementType
    element_id: int
    def __init__(self, type: _Optional[_Union[UIElementType, str]] = ..., element_id: _Optional[int] = ...) -> None: ...

class UIElementTree(_message.Message):
    __slots__ = ("element_id", "visible", "elements")
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    visible: bool
    elements: _containers.RepeatedCompositeFieldContainer[UIElementTreeEntry]
    def __init__(self, element_id: _Optional[int] = ..., visible: _Optional[bool] = ..., elements: _Optional[_Iterable[_Union[UIElementTreeEntry, _Mapping]]] = ...) -> None: ...

class UIElementTrees(_message.Message):
    __slots__ = ("etrees",)
    ETREES_FIELD_NUMBER: _ClassVar[int]
    etrees: _containers.RepeatedCompositeFieldContainer[UIElementTree]
    def __init__(self, etrees: _Optional[_Iterable[_Union[UIElementTree, _Mapping]]] = ...) -> None: ...

class MappedElementTrees(_message.Message):
    __slots__ = ("element_ids",)
    ELEMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    element_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, element_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class UIETreeMapping(_message.Message):
    __slots__ = ("mapping",)
    class MappingEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: MappedElementTrees
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[MappedElementTrees, _Mapping]] = ...) -> None: ...
    MAPPING_FIELD_NUMBER: _ClassVar[int]
    mapping: _containers.MessageMap[str, MappedElementTrees]
    def __init__(self, mapping: _Optional[_Mapping[str, MappedElementTrees]] = ...) -> None: ...

class UIMarkdownField(_message.Message):
    __slots__ = ("element_id", "visible", "text")
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    visible: bool
    text: str
    def __init__(self, element_id: _Optional[int] = ..., visible: _Optional[bool] = ..., text: _Optional[str] = ...) -> None: ...

class UIMarkdownFields(_message.Message):
    __slots__ = ("fields",)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIMarkdownField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIMarkdownField, _Mapping]]] = ...) -> None: ...

class UIButtonField(_message.Message):
    __slots__ = ("element_id", "visible", "text")
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    visible: bool
    text: str
    def __init__(self, element_id: _Optional[int] = ..., visible: _Optional[bool] = ..., text: _Optional[str] = ...) -> None: ...

class UIButtonFields(_message.Message):
    __slots__ = ("fields",)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIButtonField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIButtonField, _Mapping]]] = ...) -> None: ...

class NumberFieldData(_message.Message):
    __slots__ = ("value", "min", "max", "step")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    value: float
    min: float
    max: float
    step: float
    def __init__(self, value: _Optional[float] = ..., min: _Optional[float] = ..., max: _Optional[float] = ..., step: _Optional[float] = ...) -> None: ...

class SelectFieldData(_message.Message):
    __slots__ = ("mapping", "selected")
    class MappingEntry(_message.Message):
        __slots__ = ("key", "value")
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

class UIValueField(_message.Message):
    __slots__ = ("element_id", "visible", "field_type", "description", "text", "number", "boolean", "datetime", "select")
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_FIELD_NUMBER: _ClassVar[int]
    FIELD_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_FIELD_NUMBER: _ClassVar[int]
    DATETIME_FIELD_NUMBER: _ClassVar[int]
    SELECT_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    visible: bool
    field_type: FieldType
    description: str
    text: str
    number: NumberFieldData
    boolean: bool
    datetime: _timestamp_pb2.Timestamp
    select: SelectFieldData
    def __init__(self, element_id: _Optional[int] = ..., visible: _Optional[bool] = ..., field_type: _Optional[_Union[FieldType, str]] = ..., description: _Optional[str] = ..., text: _Optional[str] = ..., number: _Optional[_Union[NumberFieldData, _Mapping]] = ..., boolean: _Optional[bool] = ..., datetime: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., select: _Optional[_Union[SelectFieldData, _Mapping]] = ...) -> None: ...

class UIValueFields(_message.Message):
    __slots__ = ("fields",)
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.RepeatedCompositeFieldContainer[UIValueField]
    def __init__(self, fields: _Optional[_Iterable[_Union[UIValueField, _Mapping]]] = ...) -> None: ...

class UIElementUpdate(_message.Message):
    __slots__ = ("element_type", "element_id", "etree", "markdown", "button", "value")
    ELEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ETREE_FIELD_NUMBER: _ClassVar[int]
    MARKDOWN_FIELD_NUMBER: _ClassVar[int]
    BUTTON_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    element_type: UIElementType
    element_id: int
    etree: UIElementTree
    markdown: UIMarkdownField
    button: UIButtonField
    value: UIValueField
    def __init__(self, element_type: _Optional[_Union[UIElementType, str]] = ..., element_id: _Optional[int] = ..., etree: _Optional[_Union[UIElementTree, _Mapping]] = ..., markdown: _Optional[_Union[UIMarkdownField, _Mapping]] = ..., button: _Optional[_Union[UIButtonField, _Mapping]] = ..., value: _Optional[_Union[UIValueField, _Mapping]] = ...) -> None: ...

class UIData(_message.Message):
    __slots__ = ("mappings", "etrees", "markdown", "buttons", "values")
    MAPPINGS_FIELD_NUMBER: _ClassVar[int]
    ETREES_FIELD_NUMBER: _ClassVar[int]
    MARKDOWN_FIELD_NUMBER: _ClassVar[int]
    BUTTONS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    mappings: UIETreeMapping
    etrees: UIElementTrees
    markdown: UIMarkdownFields
    buttons: UIButtonFields
    values: UIValueFields
    def __init__(self, mappings: _Optional[_Union[UIETreeMapping, _Mapping]] = ..., etrees: _Optional[_Union[UIElementTrees, _Mapping]] = ..., markdown: _Optional[_Union[UIMarkdownFields, _Mapping]] = ..., buttons: _Optional[_Union[UIButtonFields, _Mapping]] = ..., values: _Optional[_Union[UIValueFields, _Mapping]] = ...) -> None: ...

class UIPage(_message.Message):
    __slots__ = ("element_id", "parent_name", "name")
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    element_id: int
    parent_name: str
    name: str
    def __init__(self, element_id: _Optional[int] = ..., parent_name: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class UIPages(_message.Message):
    __slots__ = ("pages",)
    PAGES_FIELD_NUMBER: _ClassVar[int]
    pages: _containers.RepeatedCompositeFieldContainer[UIPage]
    def __init__(self, pages: _Optional[_Iterable[_Union[UIPage, _Mapping]]] = ...) -> None: ...
