"""
User Interface Elements
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import InitVar, dataclass, field
from datetime import UTC, date, datetime, time
from functools import partial
from typing import TYPE_CHECKING, ClassVar, NamedTuple, override

from google.protobuf.timestamp_pb2 import Timestamp

from pulsarity import ctx
from pulsarity._protobuf import ui_pb2, websocket_pb2
from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.events import EvtPriority
from pulsarity.events.server import SystemEventData, system_event

if TYPE_CHECKING:
    from google.protobuf.message import Message


@system_event
class UIElementUpdate(SystemEventData):
    """
    User interface element update event
    """

    event_id: ClassVar = websocket_pb2.EVENT_UI_UPDATE
    priority: ClassVar = EvtPriority.LOW
    permission: ClassVar = SystemDefaultPerms.SIMPLEX_WEBSOCKET

    ui_element: UIElement

    def serialize_message(self) -> bytes:
        update_data = self.ui_element.to_element_update_message()
        return websocket_pb2.WebsocketEvent(
            event_id=self.event_id, ui_element_update=update_data
        ).SerializeToString()


@dataclass(frozen=True, slots=True)
class UIElement[T: Message](ABC):
    """
    User interface element abstract base class
    """

    element_type_id: ClassVar[ui_pb2.UIElementType]
    _store: ClassVar[dict[int, UIElement]]

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    _hidden: bool = field(default=False, init=False)

    permission: SystemDefaultPerms | str | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        self._store[self.uid] = self

    @property
    def hidden(self) -> bool:
        """
        Whether the element is hidden in the UI or not
        """
        return self._hidden

    @hidden.setter
    def hidden(self, val: bool):
        if val != self._hidden:
            object.__setattr__(self, "_hidden", val)
            self.publish_update_event()

    @classmethod
    def get_element_by_uid(cls, uid: int) -> UIElement[T] | None:
        """
        Get an element from the class store by uid
        """
        if uid in cls._store:
            return cls._store[uid]
        return None

    def publish_update_event(self) -> None:
        """
        Publish an UI element update event
        """
        broker = ctx.event_broker_ctx.get()
        evt = UIElementUpdate(ui_element=self)  # pylint: disable=E1123
        broker.publish(evt)

    @abstractmethod
    def element_to_message(self) -> T:
        """
        Convert the element data to message
        """

    @abstractmethod
    def to_element_update_message(self) -> ui_pb2.UIElementUpdate:
        """
        Convert the UI element data to a ui element update message
        """

    @classmethod
    def store_element_message(cls) -> Iterable[T]:
        """
        Generate element messages from the store
        """
        scopes = ctx.user_permsissions_ctx.get()
        return (
            i.element_to_message()
            for i in cls._store.values()
            if i.permission is None or i.permission in scopes
        )

    @classmethod
    @abstractmethod
    def store_to_message(cls) -> Message:
        """
        Convert the store data to message
        """


@dataclass(frozen=True, slots=True)
class UIETree(UIElement[ui_pb2.UIElementTree], Iterable[UIElement]):
    """
    User interface element tree
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_ETREE
    _store: ClassVar = {}

    _mapping_store: ClassVar[dict[str, list[UIETree]]] = defaultdict(list)

    _elements: list[UIElement] = field(default_factory=list, init=False)

    def add_element(self, element: UIElement) -> None:
        """
        Adds an element to the element tree
        """
        self._elements.append(element)

    def remove_element(self, element: UIElement) -> None:
        """
        Removes an element from the element tree
        """
        self._elements.remove(element)

    def __iter__(self):
        yield from self._elements

    def __contains__(self, key):
        return key in self._elements

    def _convert_entries(self) -> Iterable[ui_pb2.UIElementTreeEntry]:
        """
        Convert element tree entries to protocol buffer messages
        """
        scopes = ctx.user_permsissions_ctx.get()
        return (
            ui_pb2.UIElementTreeEntry(type=elem.element_type_id, element_id=elem.uid)
            for elem in self._elements
            if elem.permission is None or elem.permission in scopes
        )

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIElementTree(
            element_id=self.uid, hidden=self._hidden, elements=self._convert_entries()
        )

    def to_element_update_message(self):
        """
        Convert the UI element data to a ui element update message
        """
        etree = self.element_to_message()
        return ui_pb2.UIElementUpdate(
            element_type=self.element_type_id, element_id=self.uid, etree=etree
        )

    @classmethod
    def store_to_message(cls):
        """
        Convert the store data to message
        """
        return ui_pb2.UIElementTrees(etrees=cls.store_element_message())

    def map_to_route(self, route: str) -> None:
        """
        Maps an element tree to a provided route
        """
        if self in self._mapping_store[route]:
            msg = "Element tree already mapped to route"
            raise ValueError(msg)
        self._mapping_store[route].append(self)

    @classmethod
    def _etree_to_ids(cls, etrees: Iterable[UIETree]) -> ui_pb2.MappedElementTrees:
        ids = (i.uid for i in etrees)
        return ui_pb2.MappedElementTrees(element_ids=ids)

    @classmethod
    def mappings_to_message(cls) -> ui_pb2.UIETreeMapping:
        """
        Convert the store data to message
        """
        mapping = {k: cls._etree_to_ids(v) for k, v in cls._mapping_store.items()}
        return ui_pb2.UIETreeMapping(mapping=mapping)


@dataclass(frozen=True, slots=True)
class UIMarkdownField(UIElement[ui_pb2.UIMarkdownField]):
    """
    User interface markdown field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_MARKDOWN
    _store: ClassVar = {}

    text: str

    def to_element_update_message(self):
        """
        Convert the UI element data to a ui element update message
        """
        markdown = self.element_to_message()
        return ui_pb2.UIElementUpdate(
            element_type=self.element_type_id, element_id=self.uid, markdown=markdown
        )

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIMarkdownField(
            element_id=self.uid, hidden=self._hidden, text=self.text
        )

    @classmethod
    def store_to_message(cls):
        """
        Convert the store data to message
        """
        return ui_pb2.UIMarkdownFields(fields=cls.store_element_message())


@dataclass(frozen=True, slots=True)
class UIButtonField(UIElement[ui_pb2.UIButtonField]):
    """
    User interface button field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_BUTTON
    _store: ClassVar = {}

    text: str
    callback: Callable[[], None]

    def to_element_update_message(self):
        """
        Convert the UI element data to a ui element update message
        """
        button = self.element_to_message()
        return ui_pb2.UIElementUpdate(
            element_type=self.element_type_id, element_id=self.uid, button=button
        )

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIButtonField(
            element_id=self.uid, hidden=self._hidden, text=self.text
        )

    @classmethod
    def store_to_message(cls):
        """
        Convert the store data to message
        """
        return ui_pb2.UIButtonFields(fields=cls.store_element_message())


@dataclass(frozen=True, slots=True)
class UIValueField[T](UIElement[ui_pb2.UIValueField], ABC):
    """
    User interface value field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_VALUE
    _store: ClassVar = {}

    field_type: ClassVar[ui_pb2.FieldType]

    _value: T = field(init=False)
    default: InitVar[T | None] = None
    description: str | None = None

    def __post_init__(self, default) -> None:
        super().__post_init__()
        if default is not None:
            self._validate_value(default)
            object.__setattr__(self, "_value", default)

    @property
    def value(self) -> T:
        """
        The value of the field
        """
        return self._value

    @value.setter
    def value(self, val: T) -> None:
        if val != self._value:
            self._validate_value(val)
            object.__setattr__(self, "_value", val)

    def _validate_value(self, _: T) -> None: ...

    def to_element_update_message(self):
        """
        Convert the UI element data to a ui element update message
        """
        value = self.element_to_message()
        return ui_pb2.UIElementUpdate(
            element_type=self.element_type_id, element_id=self.uid, value=value
        )

    @classmethod
    def store_to_message(cls):
        """
        Convert the store data to message
        """
        return ui_pb2.UIValueFields(fields=cls.store_element_message())


@dataclass(frozen=True, slots=True)
class UITextValueField(UIValueField[str]):
    """
    User interface text value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_TEXT

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, str):
            msg = "Value is not a string"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            text=self.value,
        )


@dataclass(frozen=True, slots=True)
class UIPasswordValueField(UITextValueField):
    """
    User interface password value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_PASSWORD


@dataclass(frozen=True, slots=True)
class UIEmailValueField(UITextValueField):
    """
    User interface email value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_EMAIL


@dataclass(frozen=True, slots=True)
class UIURLValueField(UITextValueField):
    """
    User interface URL value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_URL


@dataclass(frozen=True, slots=True)
class UITelValueField:
    """
    User interface telephone value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_TEL


@dataclass(frozen=True, slots=True)
class UINumberValueField(UIValueField[float]):
    """
    User interface number value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_NUMBER

    min: float | None = None
    max: float | None = None
    step: float | None = None

    @override
    def _validate_value(self, value):
        if not isinstance(value, float):
            msg = "Value is not a number"
            raise TypeError(msg)

        msg = "Value outside of set parameters"

        if self.min is not None:
            if value < self.min:
                raise ValueError(msg)

            if self.step is not None and (value - self.min) % self.step:
                raise ValueError(msg)

            return

        if self.max is not None and value > self.max:
            raise ValueError(msg)

        if self.step is not None and value % self.step:
            raise ValueError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        number = ui_pb2.NumberFieldData(
            value=self.value, min=self.min, max=self.max, step=self.step
        )
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            number=number,
        )


@dataclass(frozen=True, slots=True)
class UIRangeValueField(UINumberValueField):
    """
    User interface range value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_RANGE

    min: float = 0
    max: float = 100
    step: float = 1


@dataclass(frozen=True, slots=True)
class UICheckboxValueField(UIValueField[bool]):
    """
    User interface checkbox value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_CHECKBOX

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, bool):
            msg = "Value is not a boolean"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            boolean=self.value,
        )


@dataclass(frozen=True, slots=True)
class UIDatetimeValueField(UIValueField[datetime]):
    """
    User interface datetime value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_DATETIME

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, datetime):
            msg = "Value is not a datetime"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        datetime_ = Timestamp().FromDatetime(self.value)
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            datetime=datetime_,
        )


@dataclass(frozen=True, slots=True)
class UIDateValueField(UIValueField[date]):
    """
    User interface date value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_DATE

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, date):
            msg = "Value is not a date"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        dt = datetime(
            year=self._value.year,
            month=self._value.month,
            day=self._value.day,
            tzinfo=UTC,
        )
        datetime_ = Timestamp().FromDatetime(dt)

        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            datetime=datetime_,
        )


@dataclass(frozen=True, slots=True)
class UITimeValueField(UIValueField[time]):
    """
    User interface time value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_TIME

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, time):
            msg = "Value is not a time"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        seconds = (
            (self._value.hour * 3600) + (self._value.minute * 60) + self._value.second
        )
        nanos = self._value.microsecond * 1000
        datetime_ = Timestamp(seconds=seconds, nanos=nanos)
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            datetime=datetime_,
        )


class _SelectOption[T](NamedTuple):
    """
    Named tuple for storing select option data
    """

    label: str
    value: T


@dataclass(frozen=True, slots=True)
class UISelectValueField[T](UIValueField[int]):
    """
    User interface time value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_SELECT

    _opt_counter: itertools.count = field(default_factory=itertools.count, init=False)
    _options: dict[int, _SelectOption[T]] = field(default_factory=dict, init=False)

    @property
    def selected_value(self) -> T:
        """
        The value of the current selection
        """
        return self._options[self._value].value

    @selected_value.setter
    def selected_value(self, val: T) -> None:
        current = self._options[self._value]
        if val != current.value:
            self._options[self._value] = _SelectOption(current.label, val)

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, int):
            msg = "Value is not a integer"
            raise TypeError(msg)
        if value not in self._options:
            msg = "Value not a valid option"
            raise ValueError(msg)

    def register_option(self, label: str, value: T) -> int:
        """
        Add an option to the select field

        :param label: The option label
        :param value: The option's internal value
        :return: The registered option id
        """
        id_ = next(self._opt_counter)
        self._options[id_] = _SelectOption(label, value)
        self.publish_update_event()
        return id_

    def remove_option(self, id_: int) -> None:
        """
        Removes an option from the selection field

        :param id_: The option's id
        """
        self._options.pop(id_)
        if id_ == self._value:
            first_key = next(iter(self._options))
            object.__setattr__(self, "_value", first_key)
        self.publish_update_event()

    def element_to_message(self):
        """
        Convert the element data to message
        """
        select = ui_pb2.SelectFieldData(
            mapping={id_: val.label for id_, val in self._options.items()},
            selected=self._value,
        )
        return ui_pb2.UIValueField(
            element_id=self.uid,
            hidden=self._hidden,
            description=self.description,
            field_type=self.field_type,
            select=select,
        )
