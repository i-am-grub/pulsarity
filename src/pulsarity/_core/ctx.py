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


loop_ctx: ContextVar[AbstractEventLoop] = ContextVar("loop_ctx")

event_broker_ctx: ContextVar[EventBroker] = ContextVar("event_broker_ctx")
race_manager_ctx: ContextVar[RaceManager] = ContextVar("race_manager_ctx")
timer_manager_ctx: ContextVar[TimerInterfaceManager] = ContextVar("timer_manager_ctx")

request_ctx: ContextVar[PulsarityRequest] = ContextVar("request_ctx")
websocket_ctx: ContextVar[PulsarityWebsocket] = ContextVar("websocket_ctx")
user_ctx: ContextVar[PulsarityUser] = ContextVar("user_ctx")
user_permsissions_ctx: ContextVar[set[str]] = ContextVar("user_permsissions_ctx")
