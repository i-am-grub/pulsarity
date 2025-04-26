"""
Asyncio helpers
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

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

    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func, *args, **kwargs)
