"""
Utilities for managing connections
"""

import asyncio
from typing import final


@final
class WebsocketConnTracker:
    """
    Context manager for tracking the client websocket
    connections actively connected to the server
    """

    __slots__ = ("_evt", "_num_conn")

    def __init__(self) -> None:
        self._evt = asyncio.Event()
        self._evt.set()
        self._num_conn = 0

    def __enter__(self):
        self._num_conn += 1
        self._evt.clear()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._num_conn -= 1
        if not self._num_conn:
            self._evt.set()

    async def wait_all_closed(self) -> None:
        """
        Wait for all websocket connections to close
        """
        await self._evt.wait()
