"""
Background task manager
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Coroutine, Iterable
from concurrent.futures import Future
from typing import Any

from .asyncio import ensure_async

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks
    """

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()
        self._loop: asyncio.AbstractEventLoop | None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Sets event loop to use for creating tasks

        :param loop: _description_
        """
        self._loop = loop

    def run_coroutine_from_thread(self, coro: Coroutine) -> Future:
        """
        Schedules a coroutine to run in the set event loop. Threadsafe
        when scheduling coroutines from other threads

        :param coro: The coroutine to run
        :raises RuntimeError: When an event loop is not set
        :return: A `concurrent.futures` Future
        """

        if self._loop is None:
            raise RuntimeError("Event loop not set")

        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def add_background_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Adds a background task.

        :param func: The function to run as a background task
        """

        async def _wrapper(awaitable: Awaitable):
            await awaitable

        awaitable = ensure_async(func, *args, **kwargs)
        if self._loop is not None:
            task = self._loop.create_task(_wrapper(awaitable))
        else:
            task = asyncio.create_task(_wrapper(awaitable))

        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def shutdown(self, timeout: float) -> None:
        """
        Wait for all background tasks to complete. If not completed within
        the timeout duration, raise `TimeoutError`

        :param timeout: The duration to wait for background tasks to finish
        """
        try:
            async with asyncio.timeout(timeout):
                while self._tasks:
                    await asyncio.sleep(0)

        except asyncio.TimeoutError as ex:
            await handle_timeout_trigger(ex, self._tasks)


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


background_tasks = BackgroundTaskManager()
