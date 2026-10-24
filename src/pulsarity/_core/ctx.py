"""
Application context managment
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from pulsarity._core.events.broker import EventBroker
    from pulsarity._core.race.manager import RaceManager
    from pulsarity._core.timing_interface.timer_manager import TimerInterfaceManager
    from pulsarity._core.webserver._auth import (
        PulsarityRequest,
        PulsarityUser,
        PulsarityWebsocket,
    )

# These values should be populated immediately by the application
evt_loop: AbstractEventLoop
event_broker: EventBroker
race_manager: RaceManager
timer_manager: TimerInterfaceManager

# Context values will be populated as needed (typically for api requests)
request_ctx: ContextVar[PulsarityRequest] = ContextVar("request_ctx")
websocket_ctx: ContextVar[PulsarityWebsocket] = ContextVar("websocket_ctx")
user_ctx: ContextVar[PulsarityUser] = ContextVar("user_ctx")
user_permsissions_ctx: ContextVar[set[str]] = ContextVar("user_permsissions_ctx")
