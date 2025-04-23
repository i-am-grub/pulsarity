"""
Background task manager
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from .asyncio import ensure_async

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks
    """

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def add_background_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Adds a background task.

        :param func: _description_
        """
        coro = ensure_async(func, *args, **kwargs)
        task = asyncio.create_task(coro)

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

        except asyncio.TimeoutError:
            await _cancel_tasks(self._tasks)


async def _cancel_tasks(tasks: set[asyncio.Task]) -> None:
    """
    Cancel any pending, and wait for the cancellation tocomplete

    :param tasks: Tasks to cancel
    """

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    _raise_task_exceptions(tasks)


def _raise_task_exceptions(tasks: set[asyncio.Task]) -> None:
    """
    Raise any unexpected exceptions

    :param tasks: Tasks to process
    """
    for task in tasks:
        if not task.cancelled() and (ex := task.exception()) is not None:
            raise ex


background_tasks = BackgroundTaskManager()
