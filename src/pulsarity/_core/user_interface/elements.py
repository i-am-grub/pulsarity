"""
User Interface Elements
"""

from __future__ import annotations

import datetime as dt
import itertools
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import InitVar, dataclass, field
from functools import partial
from typing import TYPE_CHECKING, ClassVar, NamedTuple, override

from google.protobuf.timestamp_pb2 import Timestamp

from pulsarity._core import ctx
from pulsarity._core._protobuf import ui_pb2, websocket_pb2
from pulsarity._core.database.permission import SystemDefaultPerms
from pulsarity._core.events import EvtPriority
from pulsarity._core.events.server import SystemEventData, system_event
from pulsarity._core.user_interface.pages import UIPage

if TYPE_CHECKING:
    from google.protobuf.message import Message

logger = logging.getLogger(__name__)


@system_event
class UIElementUpdate(SystemEventData):
    """
    User interface element update event
    """

    event_id: ClassVar = websocket_pb2.EVENT_UI_UPDATE
    priority: ClassVar = EvtPriority.LOW
    permission: ClassVar = SystemDefaultPerms.READ_WEBSOCKET

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

    visible: bool = field(default=True, init=False)

    auto_register: InitVar[bool] = field(default=False, kw_only=True)
    permission: SystemDefaultPerms | str | None = field(default=None, kw_only=True)

    def __post_init__(self, auto_register: bool) -> None:
        if auto_register:
            self.register()

    def set_visible(self) -> None:
        """
        Set the element to be visible
        """
        if not self.visible:
            object.__setattr__(self, "visible", True)
            self.publish_update_event()

    def set_invsible(self) -> None:
        """
        Set the element to be invsible
        """
        if self.visible:
            object.__setattr__(self, "visible", False)
            self.publish_update_event()

    @property
    def registered(self) -> bool:
        """
        The element's registration status
        """
        return self.uid in self._store

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

        Passes `None` as a default to prevent issues with fields
        being updated before the context is valid
        """
        evt = UIElementUpdate(ui_element=self)
        ctx.event_broker.publish(evt)

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

    def register(self) -> None:
        """
        Registers an element to be shown in the user interface.
        """
        if self.uid in self._store:
            msg = f"Element {self} is already registered for use."
            raise RuntimeError(msg)

        self._store[self.uid] = self

    def unregister(self) -> None:
        """
        Unregisters an element to be shown in the user interface.
        """
        if self.uid not in self._store:
            msg = f"Element {self} is not registered for use."
            raise RuntimeError(msg)

        self._store.pop(self.uid)

    @classmethod
    def _clear_registered(cls) -> None:
        """
        Clears the registered elements from the class store
        """
        cls._store.clear()


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
        if not self.registered:
            logger.warning("Adding an element to an unregisterd UIETree (%s)", self)

        if not element.registered:
            logger.warning("Adding an unregisterd element (%s) to an UIETree", element)

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
            element_id=self.uid, visible=self.visible, elements=self._convert_entries()
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

    def map_to_page(self, page: UIPage | str) -> None:
        """
        Maps an element tree to a provided page
        """
        if not self.registered:
            logger.warning("Mapping an unregisterd UIETree (%s) to a UIPage", self)

        if UIPage.is_name_registered(page):
            logger.warning("Mapping an UIETree to an unregisterd UIPage (%s)", page)

        if isinstance(page, UIPage):
            page = page.name

        if self in self._mapping_store[page]:
            msg = "Element tree already mapped to page"
            raise ValueError(msg)
        self._mapping_store[page].append(self)

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

    @override
    @classmethod
    def _clear_registered(cls) -> None:
        """
        Clears the registered elements from the class store
        """
        super()._clear_registered()
        cls._mapping_store.clear()


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
            element_id=self.uid, visible=self.visible, text=self.text
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
            element_id=self.uid, visible=self.visible, text=self.text
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

    _value: T | None = field(init=False, default=None)
    default: InitVar[T | None] = None
    description: str | None = None

    def __post_init__(self, auto_register: bool, default: T | None) -> None:
        if default is not None:
            self._validate_value(default)
            object.__setattr__(self, "_value", default)

        super().__post_init__(auto_register)

    @property
    def value(self) -> T | None:
        """
        The value of the field
        """
        return self._value

    @value.setter
    def value(self, val: T) -> None:
        if val != self._value:
            self._validate_value(val)
            object.__setattr__(self, "_value", val)

    def _validate_value(self, value: T) -> None: ...  # pyright: ignore[reportUnusedParameter]

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
    def _validate_value(self, value):
        if not isinstance(value, str):
            msg = "Value is not a string"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        return ui_pb2.UIValueField(
            element_id=self.uid,
            visible=self.visible,
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
class UITelValueField(UITextValueField):
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
        if not isinstance(value, (float, int)):
            msg = "Value is not a number"
            raise TypeError(msg)

        msg = "Value outside of set parameters"

        if self.min is not None:
            if value < self.min:
                raise ValueError(msg)

            if self.step is not None and (value - self.min) % self.step:
                raise ValueError(msg)

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
            visible=self.visible,
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

    _value: bool = field(init=False, default=False)
    default: InitVar[bool] = False

    @property
    @override
    def value(self) -> bool:
        """
        The value of the field
        """
        return self._value

    @value.setter
    def value(self, val: bool) -> None:
        if val != self._value:
            self._validate_value(val)
            object.__setattr__(self, "_value", val)

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
            visible=self.visible,
            description=self.description,
            field_type=self.field_type,
            boolean=self.value,
        )


@dataclass(frozen=True, slots=True)
class UIDatetimeValueField(UIValueField[dt.datetime]):
    """
    User interface datetime value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_DATETIME

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, dt.datetime):
            msg = "Value is not a datetime"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        if self._value is not None:
            datetime_ = Timestamp()
            datetime_.FromDatetime(self._value)
        else:
            datetime_ = None

        return ui_pb2.UIValueField(
            element_id=self.uid,
            visible=self.visible,
            description=self.description,
            field_type=self.field_type,
            datetime=datetime_,
        )


@dataclass(frozen=True, slots=True)
class UIDateValueField(UIValueField[dt.date]):
    """
    User interface date value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_DATE

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, dt.date):
            msg = "Value is not a date"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        if self._value is not None:
            dt_ = dt.datetime(
                year=self._value.year,
                month=self._value.month,
                day=self._value.day,
                tzinfo=dt.UTC,
            )
            datetime_ = Timestamp()
            datetime_.FromDatetime(dt_)
        else:
            datetime_ = None

        return ui_pb2.UIValueField(
            element_id=self.uid,
            visible=self.visible,
            description=self.description,
            field_type=self.field_type,
            datetime=datetime_,
        )


@dataclass(frozen=True, slots=True)
class UITimeValueField(UIValueField[dt.time]):
    """
    User interface time value field
    """

    field_type: ClassVar = ui_pb2.FIELD_TYPE_TIME

    @override
    def _validate_value(self, value) -> None:
        if not isinstance(value, dt.time):
            msg = "Value is not a time"
            raise TypeError(msg)

    def element_to_message(self):
        """
        Convert the element data to message
        """
        if self._value is not None:
            seconds = (
                (self._value.hour * 3600)
                + (self._value.minute * 60)
                + self._value.second
            )
            nanos = self._value.microsecond * 1000
            datetime_ = Timestamp(seconds=seconds, nanos=nanos)
        else:
            datetime_ = None

        return ui_pb2.UIValueField(
            element_id=self.uid,
            visible=self.visible,
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
        if self._value is None:
            msg = "Unable to get value when selection is None"
            raise ValueError(msg)

        return self._options[self._value].value

    @selected_value.setter
    def selected_value(self, val: T) -> None:
        if self._value is None:
            msg = "Unable to set value when selection is None"
            raise ValueError(msg)

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
            try:
                first_key = next(iter(self._options))
            except StopIteration:
                first_key = None

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
            visible=self.visible,
            description=self.description,
            field_type=self.field_type,
            select=select,
        )
