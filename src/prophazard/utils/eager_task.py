"""
Custom eager task management
"""

import logging
import asyncio
from collections.abc import Coroutine

logger = logging.getLogger(__name__)


def schedule_eager_task(
    time: float,
    coro: Coroutine,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
    block_duration: float = 0.0,
) -> asyncio.TimerHandle:
    """
    Schedule an eager task to be generated at a specified time. This function
    will attempt to block the event loop briefly before the scheduled time
    to schedule the race as close to the assigned time as possible.

    :param time: The time to schedule the task at
    :param coro: The coroutine to schedule
    :param loop: The event loop to use, defaults to None
    :param block_duration: The amount of time to block the event loop,
    defaults to 0.0 seconds
    :return: The timer handle
    """

    if block_duration < 0.0:
        raise ValueError("Block duration can not be negative")

    if loop is None:
        loop = asyncio.get_running_loop()

    def create_task():

        while (time_ := loop.time() - time) < 0:
            pass

        asyncio.Task(coro, loop=loop, eager_start=True)

        logger.debug("Task running at %s", f"{time_:.3f}")

    logger.debug("Task scheduled for %s", f"{time:.3f}")

    return loop.call_at(time - block_duration, create_task)


def delay_eager_task(
    delay: float,
    coro: Coroutine,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
    block_duration: float = 0.0,
) -> asyncio.TimerHandle:
    """
    Schedule an eager task to be generated in a specific amount of time.
    This function will attempt to block the event loop briefly before
    the scheduled time to schedule the race as close to the assigned time
    as possible.

    :param delay: The time in seconds to schedule the task
    :param coro: The coroutine to schedule
    :param loop: The event loop to use, defaults to None
    :param block_duration: The amount of time to block the event loop,
    defaults to 0.0 seconds
    :return: The timer handle
    """
    if loop is None:
        loop = asyncio.get_running_loop()

    time_ = loop.time() + delay

    return schedule_eager_task(time_, coro, loop=loop, block_duration=block_duration)
