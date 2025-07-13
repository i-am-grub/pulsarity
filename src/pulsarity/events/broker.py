"""
System event distribution to clients
"""

import asyncio
import bisect
import copy
import functools
import itertools
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Self

from pulsarity.events.enums import EvtPriority, _ApplicationEvt
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async


@dataclass(frozen=True)
class _QueuedEvtData:
    _counter = itertools.count()

    evt: _ApplicationEvt
    uuid: uuid.UUID
    data: dict

    _id: int = field(default_factory=partial(next, _counter))

    def __lt__(self, other: Self):
        return (self.evt.priority, self._id) < (other.evt.priority, other._id)


class EventBroker:
    """
    Manages distributing server side events to connect clients and
    triggering server side event callbacks.
    """

    counter = itertools.count()

    def __init__(self) -> None:
        """
        Class initialization
        """
        self._connections: set[asyncio.PriorityQueue[_QueuedEvtData]] = set()
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

        payload = _QueuedEvtData(event, uid, data)
        for connection in self._connections:
            connection.put_nowait(payload)

    def trigger(
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
        background.add_background_task(self._callback_runner, callbacks, data)

    async def _callback_runner(
        self, callbacks: list[tuple[int, Callable, dict[str, Any]]], data: dict
    ) -> None:
        """
        Run all procided callbacks sequentially

        :param callbacks: The list of callbacks to run
        :param data: The additional data to provide for each callback

        """
        for callback in callbacks:
            kwargs = callback[2] | data
            callable_ = callback[1]
            await ensure_async(callable_, **kwargs)

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
    ) -> AsyncGenerator[_QueuedEvtData, None]:
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
