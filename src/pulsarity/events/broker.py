"""
System event distribution to clients
"""

from asyncio import PriorityQueue
from collections.abc import AsyncGenerator, Callable
from dataclasses import astuple
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from .enums import _EvtPriority, _ApplicationEvt
from ..database.permission import UserPermission

if TYPE_CHECKING:
    from ..extensions import current_app
else:
    from quart import current_app


class EventBroker:
    """
    Manages distributing server side events to connect clients and
    triggering server side event callbacks.
    """

    def __init__(self) -> None:
        """
        Class initialization
        """
        self._connections: set[PriorityQueue] = set()
        self._callbacks: dict[str, set[Callable]] = {}

    def publish(
        self, event: _ApplicationEvt, data: dict, *, uuid: UUID | None = None
    ) -> None:
        """
        Push the event data to all subscribed clients

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        uuid_ = uuid4() if uuid is None else uuid

        payload = (*astuple(event), uuid_, data)
        for connection in self._connections:
            connection.put_nowait(payload)

    def trigger(
        self, event: _ApplicationEvt, data: dict, *, uuid: UUID | None = None
    ) -> None:
        """
        Publishes data to all subscribed clients and triggers
        all registered callbacks for the event

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        self.publish(event, data, uuid=uuid)

        if (callbacks := self._callbacks.get(event.id)) is not None:
            for callback in callbacks:
                current_app.add_background_task(callback, **data)

    def register_event_callback(self, event: _ApplicationEvt, callback: Callable):
        """
        Register a callback to run when when an event is published

        :param event_id: The id of the event to register the callback against
        :param callback: The callback to run
        """
        if event.id not in self._callbacks:
            self._callbacks[event.id] = set()

        self._callbacks[event.id].add(callback)

    def unregister_event_callback(self, event: _ApplicationEvt, callback: Callable):
        """
        Unregister an event callback

        :param event_id: The id of the event to register the callback against
        :param callback: The callback to remove
        """
        if event.id not in self._callbacks:
            return

        self._callbacks[event.id].remove(callback)

    async def subscribe(
        self,
    ) -> AsyncGenerator[tuple[_EvtPriority, UserPermission, str, UUID, dict], None]:
        """
        Subscribe to recieve server events. Typically used for client connections

        :yield: Event data
        """
        connection: PriorityQueue = PriorityQueue()
        self._connections.add(connection)
        try:
            while True:
                yield await connection.get()
        finally:
            self._connections.remove(connection)
