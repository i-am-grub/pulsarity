"""
Asyncio helpers
"""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from typing import ParamSpec, TypeVar
from concurrent.futures import Future

from pulsarity import ctx

T = TypeVar("T")
P = ParamSpec("P")


def ensure_async(func: Callable[P, T], *args, **kwargs) -> Awaitable[T]:
    """
    Ensures that the provided function is ran asynchronously

    :param func: The function to run
    :return: A generated coroutine
    """
    if asyncio.iscoroutinefunction(func):
        return func(*args, **kwargs)

    return ctx.loop_ctx.get().run_in_executor(None, func, *args, **kwargs)


def run_coroutine_from_thread(coro: Coroutine) -> Future:
    """
    Schedules a coroutine to run in the set event loop. Threadsafe
    when scheduling coroutines from other threads

    :param coro: The coroutine to run
    :raises RuntimeError: When an event loop is not set
    :return: A `concurrent.futures` Future
    """

    return asyncio.run_coroutine_threadsafe(coro, ctx.loop_ctx.get())
