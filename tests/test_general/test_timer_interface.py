import asyncio
import time
import uuid

import pytest

from pulsarity.interface import TimerData, TimerMode
from pulsarity.interface.timer_manager import TimerInterfaceManager


@pytest.fixture(name="interface_manager")
def _interface_manager():
    yield TimerInterfaceManager()


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


def test_register_interface_error(interface_manager: TimerInterfaceManager):
    """
    Test for registration of a bad interface
    """

    with pytest.raises(RuntimeError):
        interface_manager.register(BadTimerInterface)


def test_register_interface_duplicate_error(interface_manager: TimerInterfaceManager):
    """
    Test for the registration of duplicate interfaces
    """

    interface_manager.register(TestTimerInterface)
    with pytest.raises(RuntimeError):
        interface_manager.register(TestTimerInterface)


def test_unregister_interface(interface_manager: TimerInterfaceManager):
    """
    Test unregistering an interface
    """
    interface_manager.register(TestTimerInterface)
    interface_manager.unregister(TestTimerInterface.identifier)


def test_unregister_interface_error(interface_manager: TimerInterfaceManager):
    """
    Test unregister an interface that wasn't registered
    """

    with pytest.raises(KeyError):
        interface_manager.unregister(TestTimerInterface.identifier)


def test_already_instantiated_interface(interface_manager: TimerInterfaceManager):
    """
    Test multiple instantiation of interface with the same data
    """
    interface_manager.register(TestTimerInterface)
    uuid_ = uuid.uuid4()
    interface_manager.instantiate_interface(
        TestTimerInterface.identifier, TimerMode.PRIMARY, uuid_=uuid_
    )

    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.identifier, TimerMode.PRIMARY, uuid_=uuid_
        )


def test_instantiate_interface_error(interface_manager: TimerInterfaceManager):
    """
    Tests instantiating an interface that wasn't previously registered
    """
    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.identifier, TimerMode.PRIMARY
        )


@pytest.mark.asyncio
async def test_manager_lifespan(interface_manager: TimerInterfaceManager):
    """
    Tests the lifespan of the interface manager
    """
    interface_manager.start()
    await interface_manager.shutdown(0.5)


@pytest.mark.asyncio
async def test_manager_register_decorator(interface_manager: TimerInterfaceManager):
    """
    Tests the usage of the `interface_manager.register` method
    as a decorator
    """
    # pylint: disable=C0115,W0612,W0212

    interface_manager = TimerInterfaceManager()

    num_interfaces = len(interface_manager._interfaces)
    assert num_interfaces == 0

    @interface_manager.register
    class SubClass(TestTimerInterface): ...

    assert len(interface_manager._interfaces) != num_interfaces
