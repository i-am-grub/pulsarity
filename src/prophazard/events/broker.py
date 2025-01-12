"""
System event distribution to clients
"""

from asyncio import PriorityQueue
from collections.abc import AsyncGenerator, Callable
from dataclasses import astuple
from uuid import UUID, uuid4

from quart import current_app

from ._enums import _EvtPriority, _ApplicationEvt
from ..database.user import UserPermission


class EventBroker:
    """
    Manages distributing server side events to connect clients.
    Primarily used with websockets or server sent events.
    """

    _connections: set[PriorityQueue] = set()
    _callbacks: dict[str, set[Callable]] = {}

    def publish(
        self, event: _ApplicationEvt, data: dict, *, uuid: UUID | None = None
    ) -> None:
        """
        Push the event data to all subscribed clients

        :param _ApplicationEvt event: Event type
        :param dict data: Event data
        :param UUID uuid: Message uuid, defaults to None
        """
        uuid_ = uuid4() if uuid is None else uuid

        payload = (*astuple(event), uuid_, data)
        for connection in self._connections:
            current_app.add_background_task(connection.put, payload)

    def trigger(
        self, event: _ApplicationEvt, data: dict, *, uuid: UUID | None = None
    ) -> None:
        """
        Publishes data to all subscribed clients and triggers
        all registered callbacks for the event

        :param _ApplicationEvt event: Event type
        :param dict data: Event data
        :param UUID uuid: Message uuid, defaults to None
        """
        self.publish(event, data, uuid=uuid)

        if (callbacks := self._callbacks.get(event.id)) is not None:
            for callback in callbacks:
                current_app.add_background_task(callback, **data)

    def register_event_callback(self, event_id: str, callback: Callable):
        """
        Register a ballback to run when when an event is published

        :param event_id: The id of the event to register the callback against
        :param callback: The callback to run
        """
        if event_id not in self._callbacks:
            self._callbacks[event_id] = set()

        self._callbacks[event_id].add(callback)

    async def subscribe(
        self,
    ) -> AsyncGenerator[tuple[_EvtPriority, UserPermission, str, UUID, dict], None]:
        """
        As a client, subscribe to recieve server events.

        :yield AsyncGenerator[tuple[_EvtPriority, UserPermission, str, UUID, dict], None]:
        Event data
        """
        connection: PriorityQueue = PriorityQueue()
        self._connections.add(connection)
        try:
            while True:
                yield await connection.get()
        finally:
            self._connections.remove(connection)
