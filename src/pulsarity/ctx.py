"""
Application context managment
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from starlette.requests import Request
    from starlette.websockets import WebSocket

    from pulsarity.events.broker import EventBroker
    from pulsarity.interface.timer_manager import TimerInterfaceManager
    from pulsarity.race.manager import RaceManager
    from pulsarity.webserver._auth import PulsarityUser


loop_ctx: ContextVar[AbstractEventLoop] = ContextVar("loop_ctx")

event_broker_ctx: ContextVar[EventBroker] = ContextVar("event_broker_ctx")
race_manager_ctx: ContextVar[RaceManager] = ContextVar("race_manager_ctx")
timer_manager_ctx: ContextVar[TimerInterfaceManager] = ContextVar("timer_manager_ctx")

request_ctx: ContextVar[Request] = ContextVar("request_ctx")
websocket_ctx: ContextVar[WebSocket] = ContextVar("websocket_ctx")
user_ctx: ContextVar[PulsarityUser] = ContextVar("user_ctx")
user_permsissions_ctx: ContextVar[set[str]] = ContextVar("user_permsissions_ctx")
