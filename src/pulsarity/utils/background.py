"""
Background task manager
"""

import asyncio
import logging
import sys
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks
    """

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def _ensure_async(self, func: Callable, *args: Any, **kwargs: Any) -> Coroutine:
        """
        Ensures the provided function is ran as a coroutine.

        :param func: The function to ensure
        :return: The generated coroutine
        """
        if asyncio.iscoroutinefunction(func):
            return func(*args, **kwargs)

        return asyncio.to_thread(func, *args, **kwargs)

    def add_background_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Adds a background task.

        :param func: _description_
        """
        coro = self._ensure_async(func, *args, **kwargs)
        task = asyncio.create_task(coro)

        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def schedule_background_task(
        self, time: float, func: Callable, *args: Any, **kwargs: Any
    ) -> asyncio.TimerHandle:
        """
        Schedules a background task to occur at a specific time with
        app context. The task will be generated as an eager task if
        possible and block the event loop slightly before it is
        scheduled to attempt to be as accurate as possible.

        :param time: The event loop time to schedule the task for
        :param func: The function to schedule

        :return: The schedule timer handler
        """
        # pylint: disable=E1101,W0718

        def _create_task() -> None:

            while (time_ := loop.time() - time) < 0:
                pass

            coro = self._ensure_async(func, *args, **kwargs)

            if sys.version_info >= (3, 12):
                task = asyncio.eager_task_factory(loop, coro)
            else:
                task = asyncio.create_task(coro)

            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

            logger.debug(
                "Task scheduled for %s, running at %s", f"{time:.3f}", f"{time_:.3f}"
            )

        loop = asyncio.get_running_loop()

        if time < loop.time():
            raise ValueError("Scheduled time is in the past")

        return loop.call_at(time - 0.05, _create_task)

    def delay_background_task(
        self, delay: float, func: Callable, *args: Any, **kwargs: Any
    ) -> asyncio.TimerHandle:
        """
        Schedules a task to be ran x seconds in the future. See `schedule_background_task`
        for more information.

        :param delay: Amount of seconds in the future to schdule the task
        :param fuction: The function to schedule
        :return: The schedule timer handler
        """
        loop = asyncio.get_running_loop()
        time = loop.time() + delay
        return self.schedule_background_task(time, func, *args, **kwargs)

    async def shutdown(self, timeout: float) -> None:
        """
        Wait for all background tasks to complete. If not completed within
        the timeout duration, raise `TimeoutError`

        :param timeout: The duration to wait for background tasks to finish
        """
        try:
            async with asyncio.timeout(timeout):
                await asyncio.gather(*self._tasks)

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
