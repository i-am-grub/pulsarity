"""
Event callbacks
"""

import functools
from typing import TYPE_CHECKING, Any

from pulsarity._core import ctx
from pulsarity._core.events import EventBroker, EvtPriority
from pulsarity._core.events.enums import SystemEvt

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = (
    "EvtPriority",
    "SystemEvt",
    "register_as_callback",
    "register_event_callback",
    "unregister_event_callback",
)


def register_event_callback(
    callback: Callable,
    event: SystemEvt,
    *,
    priority: EvtPriority = EvtPriority.LOWEST,
    default_kwargs: dict[str, Any] | None = None,
) -> None:
    ctx.event_broker.register_event_callback(
        callback, event, priority=priority, default_kwargs=default_kwargs
    )


register_event_callback.__doc__ = EventBroker.register_event_callback.__doc__


def unregister_event_callback(
    callback: Callable,
    event: SystemEvt,
) -> None:
    ctx.event_broker.unregister_event_callback(callback, event)


unregister_event_callback.__doc__ = EventBroker.unregister_event_callback.__doc__


def register_as_callback(
    event: SystemEvt,
    *,
    priority: EvtPriority = EvtPriority.LOWEST,
    default_kwargs: dict[str, Any] | None = None,
):
    """
    Decorator for registing a callback function for an event on module
    import.

    :param event: The id of the event to register the callback against
    :param priority: The priority associated with scheduling the callback.
    :param default_kwargs: Default key word arguments to use and/or include
    when the event is triggered
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
