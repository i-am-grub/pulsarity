"""
Element Trees
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import lru_cache, partial
from typing import TYPE_CHECKING, ClassVar, Self

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
class UIElement(ABC):
    """
    User interface element abstract base class
    """

    element_type_id: ClassVar[ui_pb2.UIElementType]
    _store: ClassVar[dict[int, Self]]

    _counter: ClassVar = itertools.count()
    uid: int = field(default_factory=partial(next, _counter), init=False)

    def __post_init__(self) -> None:
        self._store[self.uid] = self

    @classmethod
    def get_element_by_uid(cls, uid: int) -> Self | None:
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
    def to_element_update_message(self) -> ui_pb2.UIElementUpdate:
        """
        Convert the UI element data to a ui element update message
        """

    @classmethod
    @abstractmethod
    def store_to_messages(cls) -> Message:
        """
        Convert the store data to message
        """


@dataclass(frozen=True, slots=True)
class UIETree(UIElement, Iterable):
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
        self.store_to_messages.cache_clear()

    def remove_element(self, element: UIElement) -> None:
        """
        Removes an element from the element tree
        """
        self._elements.remove(element)
        self.store_to_messages.cache_clear()

    def __iter__(self) -> Iterable[UIElement]:
        return self._elements.__iter__()

    def __contains__(self, key):
        return self._elements.__contains__(key)

    @classmethod
    def _elements_to_entries(
        cls, elements: Iterable[UIETree]
    ) -> Iterable[ui_pb2.UIElementTreeEntry]:
        return (
            ui_pb2.UIElementTreeEntry(type=i.element_type_id, element_id=i.uid)
            for i in elements
        )

    def to_element_update_message(self):
        entries = self._elements_to_entries(self)
        etree = ui_pb2.UIElementTree(element_id=self.uid, elements=entries)
        return ui_pb2.UIElementUpdate(
            element_type=self.element_type_id, element_id=self.uid, etree=etree
        )

    @classmethod
    @lru_cache
    def store_to_messages(cls):
        """
        Convert the store data to message
        """
        etrees = (
            ui_pb2.UIElementTree(element_id=i.uid, elements=cls._elements_to_entries(i))
            for i in cls._store.values()
        )
        return ui_pb2.UIElementTrees(etrees=etrees)

    def map_to_route(self, route: str) -> None:
        """
        Maps an element tree to a provided route
        """
        if self in self._mapping_store[route]:
            msg = "Element tree already mapped to route"
            raise ValueError(msg)
        self._mapping_store[route].append(self)
        self.mappings_to_message.cache_clear()

    @classmethod
    def _etree_to_ids(cls, etrees: Iterable[UIETree]) -> ui_pb2.MappedElementTrees:
        ids = (i.uid for i in etrees)
        return ui_pb2.MappedElementTrees(element_ids=ids)

    @classmethod
    @lru_cache
    def mappings_to_message(cls) -> ui_pb2.UIETreeMapping:
        """
        Convert the store data to message
        """
        mapping = {k: cls._etree_to_ids(v) for k, v in cls._mapping_store.items()}
        return ui_pb2.UIETreeMapping(mapping=mapping)


@dataclass(frozen=True, slots=True)
class UIMarkdownField(UIElement):
    """
    User interface markdown field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_MARKDOWN
    _store: ClassVar = {}


@dataclass(frozen=True, slots=True)
class UIButtonField(UIElement):
    """
    User interface button field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_BUTTON
    _store: ClassVar = {}


@dataclass(frozen=True, slots=True)
class UIValueField(UIElement):
    """
    User interface value field
    """

    element_type_id: ClassVar = ui_pb2.ELEMENT_TYPE_VALUE
    _store: ClassVar = {}
