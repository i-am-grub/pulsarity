from asyncio import PriorityQueue, TaskGroup
from collections.abc import AsyncGenerator
from dataclasses import astuple


from ._enums import _EvtPriority, _ApplicationEvt
from ..database.user import UserPermission


class EventBroker:
    """
    Manages distributing server side events to connect clients.
    Primarily used with websockets or server sent events.
    """

    _connections: set[PriorityQueue] = set()

    async def publish(self, event: _ApplicationEvt, data: dict) -> None:
        async with TaskGroup() as tg:
            for connection in self._connections:
                payload = (*astuple(event), data)
                tg.create_task(connection.put(payload))

    async def subscribe(
        self,
    ) -> AsyncGenerator[tuple[_EvtPriority, UserPermission, str, dict], None]:
        connection: PriorityQueue = PriorityQueue()
        self._connections.add(connection)
        try:
            while True:
                yield await connection.get()
        finally:
            self._connections.remove(connection)
