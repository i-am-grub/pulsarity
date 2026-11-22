"""Background task manager."""

import logging
from typing import TYPE_CHECKING, Any

from pulsarity._core import ctx
from pulsarity._core.utils.asyncio import (
    ensure_async,
    wait_task_cancellation,
)

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Awaitable, Callable


logger = logging.getLogger(__name__)


_tasks: set[asyncio.Task] = set()


def add_background_task[T](
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> asyncio.Task[T]:
    """Adds a background task.

    Args:
        func: The function to run
        args: The positional arguments
        kwargs: The keyword arguments

    Returns:
        A generated coroutine
    """

    async def _wrapper(awaitable: Awaitable[T]) -> T:
        return await awaitable

    awaitable = ensure_async(func, *args, **kwargs)

    task = ctx.evt_loop.create_task(_wrapper(awaitable))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)

    return task


def add_pregenerated_task(task: asyncio.Task):
    """Adds a pre-generated task.

    Typically used to make sure tasks are shutdown with the server.

    Args:
        task: The task to add to the background manager
    """
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def shutdown(timeout: float) -> None:  # noqa: ASYNC109
    """Wait for all background tasks to complete.

    If not completed within the timeout duration, raise `TimeoutError`.

    Args:
        timeout: The duration to wait for background tasks to finish
    """
    msg = "Error encountered in background task"
    await wait_task_cancellation(_tasks, msg, timeout=timeout)
