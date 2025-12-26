"""
Abstract timer interface
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", bound=int | str | bool | Enum)


@dataclass(frozen=True)
class TimerData:
    """
    Parent class for incoming timer data
    """

    timestamp: float
    """The time of processing the value"""
    timer_identifier: str
    """Identifier of the origin interface"""
    node_index: int
    """Index of the node"""
    value: float
    """The data value"""


@dataclass(frozen=True)
class TimerSetting(Generic[T]):
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
    settings: Sequence[TimerSetting]
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
    settings: Sequence[TimerSetting]
    """Interface settings"""
    actions: Sequence[Action]
    """Interface actions"""
    connected: bool
    """Connection status"""

    def subscribe(
        self,
        lap_queue: asyncio.Queue[TimerData],
        signal_queue: asyncio.Queue[TimerData],
    ) -> None:
        """
        Subscribe to recieve lap and signal data from the interface

        :param lap_queue: The queue to provide for recieving lap data
        :param signal_queue: The queue to provide for recieving signal data
        """

    def shutdown(self):
        """
        Shutdown the interface connection. When called, prevent adding more data to
        the lap and signal queues.
        """
