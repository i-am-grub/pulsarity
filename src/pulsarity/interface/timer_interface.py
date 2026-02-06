"""
Abstract timer interface
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, NamedTuple, Protocol, TypeVar, runtime_checkable

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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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
        lap_queue: asyncio.Queue[BasicLapData],
        signal_queue: asyncio.Queue[BasicSignalData],
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
