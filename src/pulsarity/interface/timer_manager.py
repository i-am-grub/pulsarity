"""
Manage timer interfaces
"""

import uuid
from dataclasses import dataclass
from enum import IntEnum, auto

from .timer_interface import TimerInterface


class TimerMode(IntEnum):
    """
    The different modes a timer can registered as
    """

    PRIMARY = auto()
    """The primary timer for scoring"""
    SPLIT = auto()
    """Timer to support split laps"""
    FAILOVER = auto()
    """A failover in the event the primary fails"""


@dataclass
class ActiveTimer:
    """
    Timer interfaces with an active connection
    """

    interface: TimerInterface
    """The timer's interface"""
    mode: TimerMode
    """The mode the timer is in"""
    index: int
    """The index of the timer. Used for ordering split timers"""


class TimerManager:
    """
    Manages the abstract and active timer interfaces
    """

    def __init__(self) -> None:
        self._interfaces: dict[str, type[TimerInterface]] = {}
        self._active_interfaces: dict[str, ActiveTimer] = {}

    def register(self, interface: type[TimerInterface]) -> None:
        """
        Registers an interface type to be used by the system

        :param interface: The
        :raises RuntimeError: _description_
        """
        if interface.identifier in self._interfaces:
            raise RuntimeError("Interface with matching identifier already registered")

        if isinstance(interface, TimerInterface):
            self._interfaces[interface.identifier] = interface

        else:
            raise RuntimeError("Attempted to register an invalid timer interface")

    def unregister(self, identifier: str) -> None:
        """
        Unregisters an interface from the system

        :param identifier: The identifier of the interface
        """
        self._interfaces.pop(identifier)

    def instantiate_interface(
        self,
        identifier: str,
        mode: TimerMode,
        index: int = 0,
        *,
        uuid_: uuid.UUID | None = None,
    ):
        """
        Creates an instance from a defined interface

        :param identifier: The identifer of the abstract interface
        :param mode: The mode to use for the interface
        :param location: Location of the timer, defaults to 0
        :param uuid_: Internal identifer of the instance, defaults to None
        """
        interface = self._interfaces.get(identifier)
        if interface is not None:
            if uuid_ is None:
                uuid_ = uuid.uuid4()

            self._active_interfaces[uuid_.hex] = ActiveTimer(
                interface=interface(), mode=mode, index=index
            )

    def decommission_interface(self, uuid_: uuid.UUID):
        """
        Decommission an interface instance

        :param identifier: The internal identifer for the interface instance
        """
        interface = self._active_interfaces.get(uuid_.hex)
        if interface is not None:
            interface.interface.shutdown()
            self._active_interfaces.pop(uuid_.hex)
