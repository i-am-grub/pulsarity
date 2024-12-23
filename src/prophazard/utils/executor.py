"""
Executor for Parallel Processing
"""

import sys
import os
import asyncio
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# pylint: disable=W0603

_executor: Future[ThreadPoolExecutor | ProcessPoolExecutor] | None = None
"""The serverwide executor pool to use for parallel computations"""


def set_executor() -> None:
    """
    Sets the global executor.

    In most cirumstances, the pool will attempt to utilize
    `os.cpu_count() - 1` to determine the number of parallel computations
    to allow at a time. Ideally, this should prevent the webserver from
    being blocked while running parallel computations.
    """
    # pylint: disable=E1101,W0212

    global _executor

    if _executor is None:
        _executor = asyncio.get_running_loop().create_future()

    if sys.version_info >= (3, 13):
        count = os.process_cpu_count()
    else:
        count = os.cpu_count()

    if sys.version_info >= (3, 13) and not sys._is_gil_enabled():
        if count is None or count <= 2:
            pool_exec = ThreadPoolExecutor(1)
        else:
            pool_exec = ThreadPoolExecutor(count - 1)
    else:
        if count is None or count <= 2:
            pool_exec = ProcessPoolExecutor(1)
        else:
            pool_exec = ProcessPoolExecutor(count - 1)

    _executor.set_result(pool_exec)


async def get_executor() -> ThreadPoolExecutor | ProcessPoolExecutor:
    """
    Get an executor to enable parallel processing for computationally
    intensive tasks. If the task to schedule in the executor is IO bound,
    consider using `asyncio.to_thread` instead.

    Returns a `ProcessPoolExecutor` under most circumstances. The exception
    providing an instance of ThreadPoolExecutor is when the python global
    interpreter lock has been disabled (experimental in python 3.13t).

    The executor should be used in the following way

    .. code-block:: python

        executor = get_executor()
        result = await loop.run_in_executor(executor, blocking_function)

    :return ThreadPoolExecutor | ProcessPoolExecutor: The instace of the pool executor
    """
    global _executor

    if _executor is None:
        _executor = asyncio.get_running_loop().create_future()

    return await _executor


async def shutdown_executor() -> None:
    """
    Wait for the executor to finish all tasks and shutdown.
    """
    if _executor is not None:
        pool_exec = await _executor
        await asyncio.to_thread(pool_exec.shutdown)
