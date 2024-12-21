"""
System event distribution to clients
"""

from asyncio import PriorityQueue, TaskGroup
from collections.abc import AsyncGenerator
from dataclasses import astuple
from uuid import UUID, uuid4


from ._enums import _EvtPriority, _ApplicationEvt
from ..database.user import UserPermission


class EventBroker:
    """
    Manages distributing server side events to connect clients.
    Primarily used with websockets or server sent events.
    """

    _connections: set[PriorityQueue] = set()

    async def publish(
        self, event: _ApplicationEvt, data: dict, *, uuid: UUID = uuid4()
    ) -> None:
        """
        Push the event data to all subscribed clients

        :param _ApplicationEvt event: Event type
        :param dict data: Event data
        :param UUID uuid: Message uuid
        """

        async with TaskGroup() as tg:
            payload = (*astuple(event), uuid, data)
            for connection in self._connections:
                tg.create_task(connection.put(payload))

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
