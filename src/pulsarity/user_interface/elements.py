"""
User Interface Elements
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property, partial
from itertools import count
from typing import TYPE_CHECKING, ClassVar, Iterable, Self, Sequence

from google.protobuf import timestamp_pb2

from pulsarity._protobuf import ui_pb2

if TYPE_CHECKING:
    from datetime import date, datetime, time

    from google.protobuf.message import Message

# pylint: disable=W0221
# ruff: noqa: RUF012


@dataclass(slots=True)
class UIElement(ABC):
    """
    Abstract base class for all user interface elements
    """

    type_: ClassVar[ui_pb2.UIElementType]
    _store: ClassVar[dict[int, Self]]
    _counter: ClassVar[count] = count()

    id: int = field(init=False, default_factory=partial(next, _counter))
    hidden: bool = field(default=False, kw_only=True)

    def __post_init__(self):
        self._store[self.id] = self

    @abstractmethod
    def model_dump(self) -> Message:
        """
        Dump the element data to a serialized protocol buffer message
        """

    @abstractmethod
    def ui_sync(self) -> None:
        """
        Synchronize the user interface to the element's state
        """

    @classmethod
    @abstractmethod
    def dump_serialized_store(cls) -> bytes:
        """
        Dump all the stored user interface elements to the a serialized
        protocol buffer message
        """


@dataclass(slots=True)
class UIETree(UIElement):
    """
    An user interface element tree
    """

    type_ = ui_pb2.ELEMENT_TYPE_ETREE
    _store = {}

    elements: Sequence[UIElement]

    def model_dump(self):
        elements = (
            ui_pb2.UIElementTreeEntry(type=e.type_, element_id=e.id)
            for e in self.elements
        )
        return ui_pb2.UIElementTree(element_id=self.id, elements=elements)

    @classmethod
    def dump_serialized_store(cls):
        etrees = (tree.model_dump() for tree in cls._store.values())
        return ui_pb2.UIElementTrees(etrees=etrees).SerializeToString()


@dataclass
class UIETreeMapping:
    """
    A mapping of where each element tree should be displayed
    within the user interface.
    """

    mapping: dict[str, Iterable[UIETree]] = field(default_factory=dict)

    @cached_property
    def dumped_model(self) -> bytes:
        """
        Cached serialized message
        """
        mapping = {
            key: ui_pb2.MappedElementTrees(element_ids=(i.id for i in trees))
            for key, trees in self.mapping.items()
        }
        return ui_pb2.UIETreeMapping(mapping=mapping).SerializeToString()

    def model_dump_protobuf(self) -> bytes:
        """
        Serialize as a protocol buffer message
        """
        return self.dumped_model


@dataclass(slots=True)
class UIMarkdown(UIElement):
    """
    A markdown element for the user interface
    """

    type_ = ui_pb2.ELEMENT_TYPE_MARKDOWN
    _store = {}

    text: str

    def model_dump(self):
        return ui_pb2.UIMarkdownField(element_id=self.id, text=self.text)

    @classmethod
    def dump_serialized_store(cls):
        fields = (field_.model_dump() for field_ in cls._store.values())
        return ui_pb2.UIMarkdownFields(fields=fields).SerializeToString()


@dataclass(slots=True)
class UIButton(UIElement):
    """
    A button element for the user interface
    """

    type_ = ui_pb2.ELEMENT_TYPE_BUTTON
    _store = {}

    text: str

    def model_dump(self):
        return ui_pb2.UIButtonField(element_id=self.id, text=self.text)

    @classmethod
    def dump_serialized_store(cls):
        fields = (field_.model_dump() for field_ in cls._store.values())
        return ui_pb2.UIButtonFields(fields=fields).SerializeToString()


@dataclass(slots=True)
class UIValueField(UIElement, ABC):
    """
    A field element ABC for the user interface
    """

    type_ = ui_pb2.ELEMENT_TYPE_FIELD
    _store = {}

    field_type: ClassVar[ui_pb2.FieldType]

    @classmethod
    def dump_serialized_store(cls):
        fields = (field_.model_dump() for field_ in cls._store.values())
        return ui_pb2.UIValueFields(fields=fields).SerializeToString()


@dataclass(slots=True)
class TextUIField(UIValueField):
    """
    Text user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_TEXT

    text: str

    def model_dump(self):
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, text=self.text
        )


@dataclass(slots=True)
class BasicIntUIField(UIValueField):
    """
    Basic integer user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_BASIC_INT

    value: int

    def model_dump(self):
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, integar=self.value
        )


@dataclass(slots=True)
class NumberUIField(UIValueField):
    """
    Number user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_NUMBER

    value: float

    def model_dump(self):
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, decimal=self.value
        )


@dataclass(slots=True)
class RangeUIField(UIValueField):
    """
    Range user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_RANGE

    min_: float
    max_: float
    value: float
    scale: float = 1.0

    def model_dump(self):
        range_data = ui_pb2.RangeData(
            min=self.min_, max=self.max_, value=self.value, scale=self.scale
        )
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, range=range_data
        )


@dataclass(slots=True)
class SelectUIField(UIValueField):
    """
    Select user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_SELECT

    def model_dump(self):
        raise NotImplementedError


@dataclass(slots=True)
class CheckboxUIField(UIValueField):
    """
    Checkbox user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_CHECKBOX

    status: bool

    def model_dump(self):
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, boolean=self.status
        )


@dataclass(slots=True)
class PasswordUIField(TextUIField):
    """
    Password user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_PASSWORD


@dataclass(slots=True)
class DateUIField(UIValueField):
    """
    Date user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_DATE

    min_: date
    max_: date
    value: date

    def model_dump(self):
        raise NotImplementedError


@dataclass(slots=True)
class TimeUIField(UIValueField):
    """
    Time user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_TIME

    value: time

    def model_dump(self):
        raise NotImplementedError


@dataclass(slots=True)
class DateTimeUIField(UIValueField):
    """
    Date user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_DATETIME

    datetime_: datetime

    def model_dump(self):
        timestamp = timestamp_pb2.Timestamp().FromDatetime(self.datetime_)
        return ui_pb2.UIValueField(
            element_id=self.id, field_type=self.field_type, datetime=timestamp
        )


@dataclass(slots=True)
class EmailTimeUIField(TextUIField):
    """
    Email user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_EMAIL


@dataclass(slots=True)
class TelephoneUIField(TextUIField):
    """
    Telephone user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_TEL


@dataclass(slots=True)
class URLUIField(TextUIField):
    """
    URL user interface field
    """

    field_type = ui_pb2.FIELD_TYPE_URL
