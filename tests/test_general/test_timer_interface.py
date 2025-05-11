import asyncio
import time
import uuid

import pytest

from pulsarity.interface import TimerData, TimerInterfaceManager, TimerMode


class BadTimerInterface: ...


class TestTimerInterface:

    identifier = "test_interface"
    display_name = "Test Interface"
    nodes = []
    settings = []
    actions = []
    connected = True
    lap_queue: asyncio.Queue[TimerData] | None = None
    rssi_queue: asyncio.Queue[TimerData] | None = None

    @property
    def num_nodes(self):
        return len(self.nodes)

    def subscribe(
        self, lap_queue: asyncio.Queue[TimerData], rssi_queue: asyncio.Queue[TimerData]
    ) -> None:
        self.lap_queue = lap_queue
        self.rssi_queue = rssi_queue

    def shutdown(self):
        self.lap_queue = None
        self.rssi_queue = None

    def add_lap(self, value: float):
        if self.lap_queue is not None:

            data = TimerData(
                timestamp=time.monotonic(),
                timer_identifier=self.identifier,
                node_index=0,
                value=value,
            )

            self.lap_queue.put_nowait(data)

    def add_rssi(self, value: float):
        if self.rssi_queue is not None:

            data = TimerData(
                timestamp=time.monotonic(),
                timer_identifier=self.identifier,
                node_index=0,
                value=value,
            )

            self.rssi_queue.put_nowait(data)


def test_register_interface_error():
    interface_manager = TimerInterfaceManager()
    with pytest.raises(RuntimeError):
        interface_manager.register(BadTimerInterface)


def test_register_interface_duplicate_error():
    interface_manager = TimerInterfaceManager()
    interface_manager.register(TestTimerInterface)
    with pytest.raises(RuntimeError):
        interface_manager.register(TestTimerInterface)


def test_unregister_interface():
    interface_manager = TimerInterfaceManager()
    interface_manager.register(TestTimerInterface)
    interface_manager.unregister(TestTimerInterface.identifier)


def test_unregister_interface_error():
    interface_manager = TimerInterfaceManager()
    with pytest.raises(KeyError):
        interface_manager.unregister(TestTimerInterface.identifier)


def test_already_instantiated_interface():
    interface_manager = TimerInterfaceManager()
    interface_manager.register(TestTimerInterface)
    uuid_ = uuid.uuid4()
    interface_manager.instantiate_interface(
        TestTimerInterface.identifier, TimerMode.PRIMARY, uuid_=uuid_
    )

    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.identifier, TimerMode.PRIMARY, uuid_=uuid_
        )


def test_instantiate_interface_error():
    interface_manager = TimerInterfaceManager()

    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.identifier, TimerMode.PRIMARY
        )


@pytest.mark.asyncio
async def test_manager_lifespan():
    interface_manager = TimerInterfaceManager()
    interface_manager.start()
    await interface_manager.shutdown(0.5)
