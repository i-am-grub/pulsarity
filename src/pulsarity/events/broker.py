"""
System event distribution to clients
"""

import asyncio
import bisect
import copy
import functools
import itertools
import logging
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import Any, Self

from pulsarity.events.enums import EvtPriority, _ApplicationEvt
from pulsarity.protobuf import websocket_pb2
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _QueuedEvtData:
    """
    Dataclass used for containing event data across the queue
    """

    evt: _ApplicationEvt
    uuid: uuid.UUID
    data: dict

    _counter = itertools.count()
    _id: int = field(default_factory=functools.partial(next, _counter))

    def __lt__(self, other: Self):
        """
        Less than comparsion. Enables the use of builtin sorting algorithms
        """
        return (self.evt.priority, self._id) < (other.evt.priority, other._id)


@dataclass(frozen=True, slots=True)
class _EvtCallbackData:
    """
    Dataclass used for containing event callback data
    """

    priority: int
    func: Callable
    default_data: dict[str, Any]

    _counter = itertools.count()
    _id: int = field(default_factory=functools.partial(next, _counter))

    def __lt__(self, other: Self):
        """
        Less than comparsion. Enables the use of builtin sorting algorithms
        """
        return (self.priority, self._id) < (other.priority, other._id)


class EventBroker:
    """
    Manages distributing server side events to connect clients and
    triggering server side event callbacks.
    """

    __slots__ = ("_connections",)

    _callbacks: dict[websocket_pb2, list[_EvtCallbackData]] = defaultdict(list)  # type: ignore

    def __init__(self) -> None:
        """
        Class initialization
        """
        self._connections: set[asyncio.PriorityQueue[_QueuedEvtData]] = set()

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
        callbacks = copy.copy(self._callbacks[event.event_id])
        await self._callback_runner(callbacks, data)

    def trigger_background(
        self,
        event: _ApplicationEvt,
        data: dict[str, Any],
        *,
        uuid_: uuid.UUID | None = None,
    ) -> None:
        """
        Publishes data to all subscribed clients and triggers
        all registered callbacks for the event in the background

        :param event: Event type
        :param data: Event data
        :param uuid: Message uuid, defaults to None
        """
        self.publish(event, data, uuid_=uuid_)
        callbacks = copy.copy(self._callbacks[event.event_id])
        background.add_background_task(self._callback_runner, callbacks, data)

    async def _callback_runner(
        self, callbacks: list[_EvtCallbackData], data: dict
    ) -> None:
        """
        Run all procided callbacks sequentially

        :param callbacks: The list of callbacks to run
        :param data: The additional data to provide for each callback
        """
        # pylint: disable=W0718

        for callback in callbacks:
            kwargs = callback.default_data | data
            try:
                await ensure_async(callback.func, **kwargs)
            except asyncio.CancelledError:
                raise
            except BaseException:
                logger.exception(
                    "Encountered error running %s as an event callback",
                    callback.func.__name__,
                )
                continue

    @classmethod
    def register_event_callback(
        cls,
        callback: Callable,
        event: _ApplicationEvt,
        *,
        priority: EvtPriority = EvtPriority.LOWEST,
        default_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a callback to run when when an event is published

        :param callback: The callback to run
        :param event: The id of the event to register the callback against
        :param priority: The priority associated with scheduling the callback.
        :param default_kwargs: Default key word arguments to use and/or include
        when the event is triggered
        """
        if default_kwargs is not None:
            default_kwargs_ = default_kwargs
        else:
            default_kwargs_ = {}

        evt_cb = _EvtCallbackData(priority, callback, default_kwargs_)
        bisect.insort_right(cls._callbacks[event.event_id], evt_cb)

    @classmethod
    def unregister_event_callback(
        cls,
        callback: Callable,
        event: _ApplicationEvt,
    ) -> None:
        """
        Unregister an event callback

        :param callback: The callback to remove
        :param event_id: The identifier of the event to register the callback against
        """
        callbacks = cls._callbacks[event.event_id]
        for callback_ in callbacks:
            if callback is callback_.func:
                callbacks.remove(callback_)
                break
        else:
            raise RuntimeError("Callback not register in system")

    @classmethod
    def clear_registered(cls) -> None:
        """
        UNIT TESTING ONLY: Clears all registered interfaces.
        """
        cls._callbacks.clear()

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
        EventBroker.register_event_callback(
            func, event, priority=priority, default_kwargs=default_kwargs
        )

        return func

    return inner
