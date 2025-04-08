"""
Executor for Parallel Processing
"""

import sys
import os
import asyncio
from asyncio import Future
from concurrent.futures import Executor, ThreadPoolExecutor, ProcessPoolExecutor


class ExecutorManager:
    """
    Manager for the system pool executor
    """

    _executor: Future[Executor] | None = None
    """The serverwide executor pool to use for parallel computations"""

    def set_executor(self) -> None:
        """
        Sets the global executor.

        In most cirumstances, the pool will attempt to utilize
        `os.cpu_count() - 1` to determine the number of parallel computations
        to allow at a time. Ideally, this should prevent the webserver from
        being blocked while running parallel computations.
        """
        # pylint: disable=E1101,W0212

        if self._executor is None:
            self._executor = asyncio.get_running_loop().create_future()
        else:
            return

        if sys.version_info >= (3, 13):
            count = os.process_cpu_count()
        else:
            count = os.cpu_count()

        count_ = min(1 if count is None or count <= 1 else count - 1, 8)
        if sys.version_info >= (3, 13) and not sys._is_gil_enabled():
            pool_exec: Executor = ThreadPoolExecutor(count_)
        else:
            pool_exec = ProcessPoolExecutor(count_)

        if not self._executor.done():
            self._executor.set_result(pool_exec)

    async def get_executor(self) -> Executor:
        """
        Get an executor to enable parallel processing for computationally
        intensive tasks. If the task to schedule in the executor is IO bound,
        consider using `asyncio.to_thread` instead.

        Returns a `ProcessPoolExecutor` under most circumstances. The exception
        providing an instance of ThreadPoolExecutor is when the python global
        interpreter lock has been disabled (experimental in python 3.13t and
        does not currently work due to incompatible dependencies).

        The executor should be used in the following way

        .. code-block:: python

            executor = get_executor()
            result = await loop.run_in_executor(executor, blocking_function)

        :return: The instace of the pool executor
        """

        if self._executor is None:
            self._executor = asyncio.get_running_loop().create_future()

        return await self._executor

    async def shutdown_executor(self) -> None:
        """
        Wait for the executor to finish all tasks and shutdown.
        """

        if self._executor is not None:
            pool_exec = await self._executor
            await asyncio.to_thread(pool_exec.shutdown)
            self._executor = None


executor = ExecutorManager()
