"""
Asyncio helpers
"""

import asyncio
import inspect
import logging
from typing import TYPE_CHECKING

from pulsarity import ctx

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Coroutine, Iterable
    from concurrent.futures import Future

logger = logging.getLogger(__name__)


def ensure_async[**P, T](func: Callable[P, T], *args, **kwargs) -> Awaitable[T]:
    """
    Ensures that the provided function is ran asynchronously

    :param func: The function to run
    :return: A generated coroutine
    """
    if inspect.iscoroutinefunction(func):
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


async def wait_task_cancellation(
    tasks: Iterable[asyncio.Task],
    exc_message: str,
    *,
    timeout: float | None = None,  # noqa: ASYNC109
) -> None:
    """
    Wait for all background tasks to complete. If not completed within
    the timeout duration, cancel the pending tasks.

    :param tasks: The tasks to
    """
    if not tasks:
        return

    _, pending = await asyncio.wait(tasks, timeout=timeout)

    for task in pending:
        task.cancel()

    await asyncio.gather(*pending, return_exceptions=True)

    for task in pending:
        if not task.cancelled() and (task_ex := task.exception()) is not None:
            logger.exception(exc_message, exc_info=task_ex)
