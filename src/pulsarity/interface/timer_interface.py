"""
Abstract timer interface
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto, unique
from typing import TYPE_CHECKING, ClassVar, Generic, NamedTuple, TypeVar

from pulsarity import ctx
from pulsarity.utils import background

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T", bound=int | str | bool | Enum)


class BasicSignalData(NamedTuple):
    """
    Tuple for passing timer signal data to
    other parts of the system
    """

    timedelta: float
    """The time of processing the value"""
    node_index: int
    """Index of the node"""
    value: float
    """The data value"""
    timer_identifier: str
    """Identifier of the origin interface"""


class BasicLapData(NamedTuple):
    """
    Tuple for passing timer lap data to
    other parts of the system
    """

    timedelta: float
    """The time of processing the value"""
    node_index: int
    """Index of the node"""
    timer_identifier: str
    """Identifier of the origin interface"""


@unique
class TimerMode(Enum):
    """
    The different modes a timer can registered as
    """

    PRIMARY = auto()
    """The primary timer for scoring"""
    SPLIT = auto()
    """Timer to support split laps"""


class FullSignalData(NamedTuple):
    """
    Tuple for passing timer signal data to
    other parts of the system
    """

    timedelta: float
    """The time of processing the value"""
    node_index: int
    """Index of the node"""
    value: float
    """The data value"""
    timer_identifier: str
    """Identifier of the origin interface"""
    timer_index: int
    """The index of the interface"""

    @property
    def timer_mode(self) -> TimerMode:
        """
        Mode of the timer
        """
        if self.timer_index:
            return TimerMode.SPLIT
        return TimerMode.PRIMARY


class FullLapData(NamedTuple):
    """
    Tuple for passing timer lap data to
    other parts of the system
    """

    timedelta: float
    """The time of processing the value"""
    node_index: int
    """Index of the node"""
    timer_identifier: str
    """Identifier of the origin interface"""
    timer_index: int
    """The index of the interface"""

    @property
    def timer_mode(self) -> TimerMode:
        """
        Mode of the timer
        """
        if self.timer_index:
            return TimerMode.SPLIT
        return TimerMode.PRIMARY


@dataclass(frozen=True, slots=True)
class TimerSetting(Generic[T]):
    """
    Interface settings
    """

    type_: type[T]
    """The type of setting"""
    callback: Callable[[int, T], None]
    """The callback to associate with the setting"""


class NodeInterface:
    """
    Node for a timing interface
    """

    class Meta:
        """Node interface metadata"""

        settings: ClassVar[dict[str, TimerSetting]] = []
        """Individual node settings"""
        actions: ClassVar[dict[str, Callable[[], None]]] = {}
        """Individual node actions"""


class TimerInterface(ABC):
    """
    Protocol for defining how timers should be integrated
    into the server.
    """

    class Meta:
        """Timer interface metadata"""

        identifier: ClassVar[str] = ""
        """Internal identifier"""
        display_name: ClassVar[str] = ""
        """Human readable identifier"""
        settings: ClassVar[dict[str, TimerSetting]] = {}
        """Interface settings"""
        actions: ClassVar[dict[str, Callable[[], None]]] = {}
        """Interface actions"""

    def __init__(
        self,
        lap_queue: asyncio.Queue[BasicLapData],
        signal_queue: asyncio.Queue[BasicSignalData],
    ):
        self._task: asyncio.Task | None = None
        self._lap_queue = lap_queue
        self._signal_queue = signal_queue
        self._nodes: dict[int, NodeInterface] = {}

    @property
    def num_nodes(self) -> int:
        """
        Number of nodes set on the interface
        """
        return len(self._nodes)

    def start(self) -> None:
        """
        Start the worker task that sends lap and signal data to the provided queues

        :param lap_queue: The queue to provide for recieving lap data
        :param signal_queue: The queue to provide for recieving signal data
        """
        if self._task is None:
            loop = ctx.loop_ctx.get()
            name = f"{self.Meta.identifier}_{id(self)}_wrapper"
            self._task = loop.create_task(self.worker, name=name)
        else:
            msg = "Timer interface already started"
            raise RuntimeError(msg)

    async def shutdown(self) -> None:
        """
        Shutdown the worker coroutine.
        """
        if self._task is not None:
            self._task.cancel()
            await self._task
            self._task = None
        else:
            msg = "Worker task is not running"
            raise RuntimeError(msg)

    @property
    @abstractmethod
    def connected(self) -> bool:
        """
        Connection status
        """

    @abstractmethod
    async def worker(self) -> None:
        """
        Worker coroutine for managing the interface communication.
        """


@dataclass(slots=True)
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

    __slots__ = (
        "_active_interfaces",
        "_lap_queue",
        "_shutdown_evt",
        "_signal_queue",
        "_tasks",
    )

    _interfaces: ClassVar[dict[str, type[TimerInterface]]] = {}

    def __init__(self) -> None:
        self._active_interfaces: dict[str, _ActiveTimer] = {}
        self._shutdown_evt = asyncio.Event()

        self._lap_queue: asyncio.Queue[BasicLapData] = asyncio.Queue()
        self._signal_queue: asyncio.Queue[BasicSignalData] = asyncio.Queue()

        self._tasks: tuple[asyncio.Task, asyncio.Task] | None = None

    def start(self) -> None:
        """
        Start the interface processing tasks
        """
        if self._tasks is not None:
            msg = "Timer instance manager already started"
            raise RuntimeError(msg)

        self._shutdown_evt.clear()

        self._tasks = (
            background.add_background_task(self._process_lap_data),
            background.add_background_task(self._process_signal_data),
        )

        for interface in self._active_interfaces.values():
            interface.interface.start()

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
            outgoing = FullLapData(
                *recieved,
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
            outgoing = FullSignalData(
                *recieved,
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

        if issubclass(interface, TimerInterface) and not inspect.isabstract(interface):
            if interface.Meta.identifier in cls._interfaces:
                msg = "Interface type with matching identifier already registered"
                raise RuntimeError(msg)

            cls._interfaces[interface.Meta.identifier] = interface

            return interface

        msg = "Attempted to register an invalid timer interface type"
        raise RuntimeError(msg)

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
                msg = "Attempted to register with an already allocated uuid"
                raise RuntimeError(msg)

            instance = interface(self._lap_queue, self._signal_queue)

            if self._tasks is not None:
                instance.start()

            index = len(self._active_interfaces)
            self._active_interfaces[uuid_.hex] = _ActiveTimer(
                interface=instance,
                index=index,
            )
        else:
            msg = "Interface class with provided identifier not registered"
            raise RuntimeError(msg)

    async def decommission_interface(self, uuid_: uuid.UUID):
        """
        Decommission an interface instance

        :param identifier: The internal identifer for the interface instance
        """
        interface = self._active_interfaces.get(uuid_.hex)
        if interface is not None:
            await interface.interface.shutdown()
            self._active_interfaces.pop(uuid_.hex)
        else:
            msg = "Interface with identifer not instantiated"
            raise RuntimeError(msg)

    async def shutdown(self, timeout: float | None = None) -> None:
        """
        Shutdown all interfaces
        """
        if self._tasks is None:
            msg = "Timer instance manager not started"
            raise RuntimeError(msg)

        for interface in self._active_interfaces.values():
            await interface.interface.shutdown()

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
