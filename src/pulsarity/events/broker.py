"""
System event distribution to clients
"""

from asyncio import PriorityQueue, iscoroutinefunction, to_thread
from bisect import insort_right
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from copy import copy, deepcopy
from dataclasses import astuple
from functools import wraps
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..database.permission import UserPermission
from .enums import EvtPriority, _ApplicationEvt

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
        self._callbacks: dict[str, list[tuple[int, Callable, dict[str, Any]]]] = (
            defaultdict(list)
        )

    def publish(
        self, event: _ApplicationEvt, data: dict[str, Any], *, uuid: UUID | None = None
    ) -> None:
        """
        Push the event data to all subscribed clients

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        uuid_ = uuid4() if uuid is None else uuid

        payload = (*astuple(event), uuid_, copy(data))
        for connection in self._connections:
            connection.put_nowait(payload)

    async def _run_callbacks(
        self, callbacks: list[tuple[int, Callable, dict[str, Any]]], data: dict
    ):
        """
        Runs all callbacks for an event sequentially. Runs non-coroutine callables
        in another thread.

        :param callbacks: The callbacks for the event
        :param data: The data to provide to each callback
        """
        for callback in callbacks:
            kwargs = callback[2] | copy(data)

            callable_ = callback[1]
            if iscoroutinefunction(callable_):
                await callable_(**kwargs)
            else:
                await to_thread(callable_, **kwargs)

    def trigger(
        self, event: _ApplicationEvt, data: dict[str, Any], *, uuid: UUID | None = None
    ) -> None:
        """
        Publishes data to all subscribed clients and triggers
        all registered callbacks for the event

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        self.publish(event, data, uuid=uuid)

        callbacks = copy(self._callbacks[event.id])
        current_app.add_background_task(self._run_callbacks, callbacks, **data)

    def register_event_callback(
        self,
        event: _ApplicationEvt,
        callback: Callable,
        *,
        priority: EvtPriority = EvtPriority.LOWEST,
        default_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a callback to run when when an event is published

        :param event: The id of the event to register the callback against
        :param callback: The callback to run
        :param priority: The priority associated with scheduling the callback.
        :param default_kwargs: Default key word arguments to use and/or include
        when the event is triggered
        """
        if default_kwargs is not None:
            default_kwargs_ = deepcopy(default_kwargs)
        else:
            default_kwargs_ = {}

        insort_right(self._callbacks[event.id], (priority, callback, default_kwargs_))

    def unregister_event_callback(
        self, event: _ApplicationEvt, callback: Callable
    ) -> None:
        """
        Unregister an event callback

        :param event_id: The identifier of the event to register the callback against
        :param callback: The callback to remove
        """
        callbacks = self._callbacks[event.id]
        for callback_ in callbacks:
            if callback is callback_[1]:
                callbacks.remove(callback_)
                break
        else:
            raise RuntimeError("Callback not register in system")

    async def subscribe(
        self,
    ) -> AsyncGenerator[tuple[EvtPriority, UserPermission, str, UUID, dict], None]:
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


event_broker = EventBroker()
"""
A module singleton instance of `EventBroker`
"""


def register_as_callback(
    event: _ApplicationEvt,
    *,
    priority: EvtPriority = EvtPriority.LOWEST,
    default_kwargs: dict[str, Any] | None = None,
):
    """
    Decorator for registing a callback function for an event

    :param event: The id of the event to register the callback against
    :param priority: The priority associated with scheduling the callback.
    :param default_kwargs: Default key word arguments to use and/or include
    when the event is triggered
    """

    @wraps
    def inner(func):
        event_broker.register_event_callback(
            event, func, priority=priority, default_kwargs=default_kwargs
        )

    return inner
