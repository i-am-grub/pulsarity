"""
System event distribution to clients
"""

import asyncio
import bisect
import copy
import dataclasses
import functools
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from typing import Any

from ..database.permission import UserPermission
from .enums import EvtPriority, _ApplicationEvt


class EventBroker:
    """
    Manages distributing server side events to connect clients and
    triggering server side event callbacks.
    """

    def __init__(self) -> None:
        """
        Class initialization
        """
        self._connections: set[asyncio.PriorityQueue] = set()
        self._callbacks: dict[str, list[tuple[int, Callable, dict[str, Any]]]] = (
            defaultdict(list)
        )

    def publish(
        self,
        event: _ApplicationEvt,
        data: dict[str, Any],
        *,
        uuid_: uuid.UUID | None = None,
    ) -> None:
        """
        Push the event data to all subscribed clients

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        uid = uuid.uuid4() if uuid_ is None else uuid_

        payload = (*dataclasses.astuple(event), uid, data)
        for connection in self._connections:
            connection.put_nowait(payload)

    async def trigger(
        self,
        event: _ApplicationEvt,
        data: dict[str, Any],
        *,
        uuid_: uuid.UUID | None = None,
    ) -> None:
        """
        Publishes data to all subscribed clients and triggers
        all registered callbacks for the event

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        self.publish(event, data, uuid_=uuid_)

        callbacks = copy.copy(self._callbacks[event.id])

        for callback in callbacks:
            kwargs = callback[2] | data

            callable_ = callback[1]
            if asyncio.iscoroutinefunction(callable_):
                await callable_(**kwargs)
            else:
                await asyncio.to_thread(callable_, **kwargs)

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
            default_kwargs_ = default_kwargs
        else:
            default_kwargs_ = {}

        bisect.insort_right(
            self._callbacks[event.id], (priority, callback, default_kwargs_)
        )

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
    ) -> AsyncGenerator[tuple[EvtPriority, UserPermission, str, uuid.UUID, dict], None]:
        """
        Subscribe to recieve server events. Typically used for client connections

        :yield: Event data
        """
        connection: asyncio.PriorityQueue = asyncio.PriorityQueue()
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

    @functools.wraps
    def inner(func):
        event_broker.register_event_callback(
            event, func, priority=priority, default_kwargs=default_kwargs
        )

    return inner
