"""
Manage timer interfaces
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass

from pulsarity import ctx
from pulsarity.interface.timer_interface import TimerData, TimerInterface
from pulsarity.utils import background

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtendedTimerData:
    """
    Dataclass for passing timer data to other parts of the
    system
    """

    timestamp: float
    """The time of processing the value"""
    timer_identifier: str
    """Identifier of the origin interface"""
    node_index: int
    """Index of the node"""
    value: float
    """The data value"""
    timer_index: int
    """The index of the interface. 0 is the PRIMARY timer"""


@dataclass
class _ActiveTimer:
    """
    Timer interfaces with an active connection
    """

    interface: TimerInterface
    """The timer's interface"""
    index: int
    """The index of the timer. Used for ordering timers. 0 is the PRIMARY timer"""


class TimerInterfaceManager:
    """
    Manages the abstract and active timer interfaces
    """

    _interfaces: dict[str, type[TimerInterface]] = {}

    def __init__(self) -> None:
        self._active_interfaces: dict[str, _ActiveTimer] = {}
        self._shutdown_evt = asyncio.Event()

        self._lap_queue: asyncio.Queue[TimerData] = asyncio.Queue()
        self._signal_queue: asyncio.Queue[TimerData] = asyncio.Queue()

        self._tasks: tuple[asyncio.Task, asyncio.Task] | None = None

    def start(self) -> None:
        """
        Start the interface processing tasks
        """
        if self._tasks is not None:
            raise RuntimeError("Timer instance manager already started")

        self._shutdown_evt.clear()

        self._tasks = (
            background.add_background_task(self._process_lap_data),
            background.add_background_task(self._process_signal_data),
        )

        for interface in self._active_interfaces.values():
            interface.interface.subscribe(self._lap_queue, self._signal_queue)

    async def _process_lap_data(self):
        """
        Add interface data to the incoming rimer data and pass
        along to the next stage

        :param manager: The manager to use for processing
        """
        race_manager = ctx.race_manager_ctx.get()

        while not self._shutdown_evt.is_set():
            recieved = await self._lap_queue.get()
            interface = self._active_interfaces[recieved.timer_identifier]
            outgoing = ExtendedTimerData(
                recieved.timestamp,
                recieved.timer_identifier,
                recieved.node_index,
                recieved.value,
                interface.index,
            )

            race_manager.status_aware_lap_record(recieved.node_index, outgoing)

    async def _process_signal_data(self):
        """
        Add interface data to the incoming rimer data and pass
        along to the next stage

        :param manager: The manager to use for processing
        """
        race_manager = ctx.race_manager_ctx.get()

        while not self._shutdown_evt.is_set():
            recieved = await self._signal_queue.get()
            interface = self._active_interfaces[recieved.timer_identifier]
            outgoing = ExtendedTimerData(
                recieved.timestamp,
                recieved.timer_identifier,
                recieved.node_index,
                recieved.value,
                interface.index,
            )

            race_manager.status_aware_signal_record(outgoing)

    @classmethod
    def register(cls, interface: type[TimerInterface]) -> None:
        """
        Registers an interface type to be used by the system

        :param interface: The
        :raises RuntimeError: Interface with matching identifier has already been
        registered
        """

        if isinstance(interface, TimerInterface):
            if interface.identifier in cls._interfaces:
                raise RuntimeError(
                    "Interface type with matching identifier already registered"
                )

            cls._interfaces[interface.identifier] = interface

            return interface

        raise RuntimeError("Attempted to register an invalid timer interface type")

    @classmethod
    def clear_registered(cls) -> None:
        """
        UNIT TESTING ONLY: Clears all registered interfaces.
        """
        cls._interfaces.clear()

    def instantiate_interface(
        self,
        identifier: str,
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
                instance.subscribe(self._lap_queue, self._signal_queue)

            index = len(self._active_interfaces)
            self._active_interfaces[uuid_.hex] = _ActiveTimer(
                interface=instance, index=index
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


def register_interface(interface_class: type[TimerInterface]) -> type[TimerInterface]:
    """
    Decorator used for registering TimerInterface classes

    :param interface_class: The timer interface class to register
    :return: The registered timer interface
    """
    TimerInterfaceManager.register(interface_class)
    return interface_class
