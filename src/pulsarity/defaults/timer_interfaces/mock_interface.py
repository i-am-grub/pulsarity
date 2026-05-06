"""
Mock timing inferface
"""

import asyncio
import math
import time
from dataclasses import dataclass
from typing import AsyncGenerator

from pulsarity.interface.timer_interface import (
    BasicSignalData,
    NodeInterface,
    TimerInterface,
    register_interface,
)

TWO_PI = 2 * math.pi
AMPLITUDE = 50.0
SHIFT = 50.0
NUM_NODES = 8
SAMPLE_RATE = 0.1


async def _delay_generator(delay: float) -> AsyncGenerator[float, None]:
    t = time.monotonic()

    while True:
        t += delay
        current_time = time.monotonic()

        if current_time < t:
            await asyncio.sleep(t - current_time)

        yield t


@dataclass(slots=True)
class MockNodeInterface(NodeInterface):
    """
    Mock Timer Node Interface
    """

    frequency: float = 0.5
    phase: float = 0.0


@register_interface
class MockTimingInterface(TimerInterface[MockNodeInterface]):
    """
    Mock Timing Interface
    """

    def __init__(self, lap_queue, signal_queue):
        super().__init__(lap_queue, signal_queue)
        for i in range(NUM_NODES):
            self._nodes[i] = MockNodeInterface()

    @property
    def connected(self):
        return self._task is not None

    async def worker(self):
        async for t in _delay_generator(SAMPLE_RATE):
            for idx, node in self._nodes.items():
                y = math.sin(TWO_PI * node.frequency * t + node.phase)
                value = AMPLITUDE * y + SHIFT
                data = BasicSignalData(0.0, idx, value, self.Meta.identifier)
                await self._signal_queue.put(data)
