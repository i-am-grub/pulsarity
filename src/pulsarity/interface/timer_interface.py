"""
Abstract timer interface
"""

from asyncio.queues import Queue
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", bound=int | str | bool | Enum)


@dataclass(frozen=True)
class LapData:
    """
    Format for lap data
    """

    index: int
    """Index of the node"""
    time: float
    """The lap time"""


@dataclass(frozen=True)
class RssiData:
    """
    Format for rssi data
    """

    index: int
    """Index of the node"""
    value: float
    """The rssi value"""


@dataclass(frozen=True)
class Setting(Generic[T]):
    """
    Interface settings
    """

    id_: str
    """Setting identifier"""
    type_: type[T]
    """The type of setting"""
    callback: Callable[[int, T], None]
    """The callback to associate with the setting"""


@dataclass(frozen=True)
class Action:
    """
    Action callback
    """

    id_: str
    """Action interface identifier"""
    callback: Callable[[], None]
    """The callback to associate with the action"""


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

    # pylint: disable=R0903

    identifier: str
    """Internal identifier"""
    display_name: str
    """Human readable identifier"""
    nodes: Sequence[NodeInterface]
    """Node associated with the timer"""
    num_nodes: int
    """Number of nodes set on the interface"""
    settings: Sequence[Setting]
    """Interface settings"""
    actions: Sequence[Action]
    """Interface actions"""
    connected: bool
    """Connection status"""

    def subscribe(self, lap_queue: Queue[LapData], rssi_queue: Queue[RssiData]) -> None:
        """
        Subscribe to recieve lap and rssi data from the interface

        :param lap_queue: The queue to provide for recieving lap data
        :param rssi_queue: The queue to provide for recieving rssi data
        """

    def shutdown(self):
        """
        Shutdown the interface connection
        """
