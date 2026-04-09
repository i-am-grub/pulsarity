from pulsarity.interface.timer_interface import (
    NodeInterface,
    TimerInterface,
    register_interface,
)


@register_interface
class MockTimingInterface(TimerInterface):
    """
    Mock Timing Interface
    """

    def __init__(self, lap_queue, signal_queue):
        super().__init__(lap_queue, signal_queue)
        for i in range(8):
            self._nodes[i] = NodeInterface()

    @property
    def connected(self):
        return self._task is not None

    async def worker(self):
        while True:
            ...
