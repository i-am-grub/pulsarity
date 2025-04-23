"""
Asyncio helpers
"""

import asyncio
from collections.abc import Callable, Coroutine
from typing import ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def ensure_async(func: Callable[P, T], *args, **kwargs) -> Coroutine[None, None, T]:
    """
    Ensures that the provided function is ran asynchronously

    :param func: The function to run
    :return: A generated coroutine
    """
    if asyncio.iscoroutinefunction(func):
        return func(*args, **kwargs)

    return asyncio.to_thread(func, *args, **kwargs)
