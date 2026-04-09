import asyncio
import time
import uuid

import pytest
from typing import ClassVar, Callable

from pulsarity.interface import BasicLapData, BasicSignalData
from pulsarity.interface.timer_interface import (
    TimerInterfaceManager,
    TimerInterface,
    TimerSetting,
)


@pytest.fixture(name="interface_manager")
def _interface_manager():
    yield TimerInterfaceManager()


class BadTimerInterface(TimerInterface): ...


class TestTimerInterface(TimerInterface):
    class Meta:
        """Timer interface metadata"""

        identifier: ClassVar[str] = "test_interface"
        """Internal identifier"""
        display_name: ClassVar[str] = "Test Interface"
        """Human readable identifier"""
        settings: ClassVar[dict[str, TimerSetting]] = {}
        """Interface settings"""
        actions: ClassVar[dict[str, Callable[[], None]]] = {}
        """Interface actions"""

    @property
    def connected(self):
        return True

    async def worker(self):
        raise TypeError()


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


def test_already_instantiated_interface(interface_manager: TimerInterfaceManager):
    """
    Test multiple instantiation of interface with the same data
    """
    interface_manager.register(TestTimerInterface)
    uuid_ = uuid.uuid4()
    interface_manager.instantiate_interface(
        TestTimerInterface.Meta.identifier, uuid_=uuid_
    )

    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.Meta.identifier, uuid_=uuid_
        )


def test_instantiate_interface_error(interface_manager: TimerInterfaceManager):
    """
    Tests instantiating an interface that wasn't previously registered
    """
    with pytest.raises(RuntimeError):
        interface_manager.instantiate_interface(
            TestTimerInterface.Meta.identifier,
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
