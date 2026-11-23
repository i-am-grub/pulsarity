"""Event callbacks."""

import functools
from typing import TYPE_CHECKING, Any

from pulsarity._core import ctx
from pulsarity._core._protobuf.websocket_pb2 import EventID
from pulsarity._core.events import EventBroker, EvtPriority

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = (
    "EventID",
    "EvtPriority",
    "register_as_callback",
    "register_event_callback",
    "unregister_event_callback",
)


def register_event_callback(
    callback: Callable,
    event: EventID,
    *,
    priority: EvtPriority = EvtPriority.LOWEST,
    default_kwargs: dict[str, Any] | None = None,
) -> None:
    """Register an event callback.

    Args:
        callback: The callback to register
        event: The event to register the callback under
        priority: The priority to give the callback. Defaults to EvtPriority.LOWEST.
        default_kwargs: The default keyword args for the callback. Defaults to None.
    """
    ctx.event_broker.register_event_callback(
        callback, event, priority=priority, default_kwargs=default_kwargs
    )


register_event_callback.__doc__ = EventBroker.register_event_callback.__doc__


def unregister_event_callback(
    callback: Callable,
    event: EventID,
) -> None:
    """Unregister an event callback.

    Args:
        callback: The callback to un-register
        event: The event to remove the callback from.
    """
    ctx.event_broker.unregister_event_callback(callback, event)


unregister_event_callback.__doc__ = EventBroker.unregister_event_callback.__doc__


def register_as_callback(
    event: EventID,
    *,
    priority: EvtPriority = EvtPriority.LOWEST,
    default_kwargs: dict[str, Any] | None = None,
):
    """Decorator for registing a callback function for an event on module import.

    Args:
        event: The id of the event to register the callback against
        priority: The priority associated with scheduling the callback.
        default_kwargs: Default key word arguments to use and/or include

    Returns:
        _description_
    """

    @functools.wraps
    def inner(func):
        EventBroker.register_event_callback(
            func,
            event,
            priority=priority,
            default_kwargs=default_kwargs,
        )

        return func

    return inner
