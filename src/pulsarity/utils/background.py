"""
Background task manager
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from pulsarity import ctx
from pulsarity.utils.asyncio import ensure_async

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

_tasks = set()


def add_background_task(
    func: Callable[..., _T], *args: Any, **kwargs: Any
) -> asyncio.Task[_T]:
    """
    Adds a background task.

    :param func: The function to run as a background task
    """

    async def _wrapper(awaitable: Awaitable[_T]) -> _T:
        return await awaitable

    awaitable = ensure_async(func, *args, **kwargs)

    task = ctx.loop_ctx.get().create_task(_wrapper(awaitable))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)

    return task


def add_pregenerated_task(task: asyncio.Task):
    """
    Adds a pre-generated task. Typically used to make sure tasks are shutdown
    with the server

    :param task: The task to add to the background manager
    """
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def shutdown(timeout: float) -> None:
    """
    Wait for all background tasks to complete. If not completed within
    the timeout duration, raise `TimeoutError`

    :param timeout: The duration to wait for background tasks to finish
    """
    try:
        async with asyncio.timeout(timeout):
            while _tasks:
                await asyncio.sleep(0)

    except asyncio.TimeoutError as ex:
        await handle_timeout_trigger(ex, _tasks)


async def handle_timeout_trigger(
    ex: asyncio.TimeoutError, tasks: Iterable[asyncio.Task]
):
    """
    Processes background tasks in the occurance of
    a timeout exception

    :param ex: The timeout exception
    :param tasks: The tasks to manage
    """

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    for task in tasks:
        if not task.cancelled() and (task_ex := task.exception()) is not None:
            raise task_ex from ex
