"""
Abstract timer interface
"""

from asyncio.queues import Queue
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable
from uuid import UUID

T = TypeVar("T", bound=int | str | bool | Enum)


@dataclass(frozen=True)
class LapData:
    """
    Format for lap data
    """

    index: int
    time: float


@dataclass(frozen=True)
class RssiData:
    """
    Format for rssi data
    """

    index: int
    value: float


@dataclass(frozen=True)
class Setting(Generic[T]):
    """
    Interface settings
    """

    id_: str
    type_: type[T]
    callback: Callable[[int, T], None]


@dataclass(frozen=True)
class Control:
    """
    Control callback
    """

    id_: str
    callback: Callable[[], None]


@runtime_checkable
class NodeInterface(Protocol):
    """
    Protocol for defining how nodes on a timing interface should
    be integrated.
    """

    # pylint: disable=R0903

    index: int
    """Index of the node"""
    settings: Sequence[Setting]
    """Individual node settings"""


@runtime_checkable
class TimerInterface(Protocol):
    """
    Protocol for defining how timers should be integrated
    into the server.
    """

    identifier: UUID
    """Identifier assigned to the interface upon ititalization"""
    nodes: Sequence[NodeInterface]
    """Node associated with the timer"""
    num_nodes: int
    """Number of nodes set on the interface"""
    settings: Sequence[Setting]
    """Interface settings"""
    controls: Sequence[Control]
    """Interface controls"""
    connected: bool
    """Connection status"""

    async def process_laps(self, queue: Queue[LapData]) -> None:
        """
        Process incoming lap data and add it to the provided queue
        """

    async def process_rssi(self, queue: Queue[RssiData]) -> None:
        """
        Process incoming rssi data and add it to the provided queue
        """
