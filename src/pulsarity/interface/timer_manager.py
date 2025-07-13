"""
Manage timer interfaces
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from dataclasses import astuple, dataclass, field
from enum import IntEnum, auto

from pulsarity.interface.timer_interface import TimerData, TimerInterface
from pulsarity.utils import background

logger = logging.getLogger(__name__)


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


_ExtendedTimerData = tuple[float, str, int, float, TimerMode, int]


@dataclass
class _ActiveTimer:
    """
    Timer interfaces with an active connection
    """

    interface: TimerInterface
    """The timer's interface"""
    mode: TimerMode
    """The mode the timer is in"""
    index: int
    """The index of the timer. Used for ordering split timers"""


@dataclass
class _DataManager:
    queue: asyncio.Queue[TimerData] = field(default_factory=asyncio.Queue)
    connections: set[asyncio.Queue[_ExtendedTimerData]] = field(default_factory=set)


class TimerInterfaceManager:
    """
    Manages the abstract and active timer interfaces
    """

    def __init__(self) -> None:
        self._interfaces: dict[str, type[TimerInterface]] = {}
        self._active_interfaces: dict[str, _ActiveTimer] = {}
        self._shutdown_evt = asyncio.Event()

        self._lap_manager = _DataManager()
        self._rssi_manager = _DataManager()

        self._tasks: tuple[asyncio.Task, asyncio.Task] | None = None

    def start(self) -> None:
        """
        Start the interface processing tasks
        """
        if self._tasks is not None:
            raise RuntimeError("Timer instance manager already started")

        self._shutdown_evt.clear()

        lap_task = background.add_background_task(
            self._process_queue_data, self._lap_manager
        )

        rssi_task = background.add_background_task(
            self._process_queue_data, self._rssi_manager
        )

        self._tasks = (lap_task, rssi_task)

        for interface in self._active_interfaces.values():
            interface.interface.subscribe(
                self._lap_manager.queue, self._rssi_manager.queue
            )

    async def subscribe_laps(self) -> AsyncGenerator[_ExtendedTimerData, None]:
        """
        Subscribe to the incoming lap data
        """
        connection: asyncio.Queue[_ExtendedTimerData] = asyncio.Queue()
        self._lap_manager.connections.add(connection)
        try:
            while not self._shutdown_evt.is_set():
                yield await connection.get()
        finally:
            self._lap_manager.connections.remove(connection)

    async def subscribe_rssi(self) -> AsyncGenerator[_ExtendedTimerData, None]:
        """
        Subscribe to the incoming rssi data
        """
        connection: asyncio.Queue[_ExtendedTimerData] = asyncio.Queue()
        self._rssi_manager.connections.add(connection)
        try:
            while not self._shutdown_evt.is_set():
                yield await connection.get()
        finally:
            self._rssi_manager.connections.remove(connection)

    async def _process_queue_data(self, manager: _DataManager):
        """
        Add interface data to the incoming rimer data and pass
        along to the next stage

        :param manager: The manager to use for processing
        """

        while not self._shutdown_evt.is_set():
            recieved = await manager.queue.get()
            interface = self._active_interfaces[recieved.timer_identifier]
            outgoing = (*astuple(recieved), interface.mode, interface.index)

            for connection in manager.connections:
                await connection.put(outgoing)

    def register(self, interface: type[TimerInterface]) -> None:
        """
        Registers an interface type to be used by the system

        :param interface: The
        :raises RuntimeError: _description_
        """

        if isinstance(interface, TimerInterface):
            if interface.identifier in self._interfaces:
                raise RuntimeError(
                    "Interface type with matching identifier already registered"
                )

            self._interfaces[interface.identifier] = interface

            return interface

        raise RuntimeError("Attempted to register an invalid timer interface type")

    def unregister(self, identifier: str) -> None:
        """
        Unregisters an interface type from the system

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
        Creates an interface instance from a registered interface type

        :param identifier: The identifer of the abstract interface
        :param mode: The mode to use for the interface
        :param location: Location of the timer, defaults to 0
        :param uuid_: Internal identifer of the instance, defaults to None
        """
        interface = self._interfaces.get(identifier)
        if interface is not None:
            if uuid_ is None:
                uuid_ = uuid.uuid4()

            if uuid_.hex in self._active_interfaces:
                raise RuntimeError(
                    "Attempted to register with an already allocated uuid"
                )

            instance = interface()

            if self._tasks is not None:
                instance.subscribe(self._lap_manager.queue, self._rssi_manager.queue)

            self._active_interfaces[uuid_.hex] = _ActiveTimer(
                interface=instance, mode=mode, index=index
            )
        else:
            raise RuntimeError(
                "Interface class with provided identifier not registered"
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
        else:
            raise RuntimeError("Interface with identifer not instantiated")

    async def shutdown(self, timeout: float | None = None) -> None:
        """
        Shutdown all interfaces
        """
        if self._tasks is None:
            raise RuntimeError("Timer instance manager not started")

        for interface in self._active_interfaces.values():
            interface.interface.shutdown()

        self._active_interfaces.clear()
        self._shutdown_evt.set()

        try:
            async with asyncio.Timeout(timeout):
                await asyncio.gather(*self._tasks)

        except asyncio.TimeoutError as ex:
            await background.handle_timeout_trigger(ex, self._tasks)

        finally:
            self._tasks = None


interface_manager = TimerInterfaceManager()
