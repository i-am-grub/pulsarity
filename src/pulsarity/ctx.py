"""
Application context managment
"""

from __future__ import annotations

from asyncio import AbstractEventLoop
from contextvars import ContextVar
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.websockets import WebSocket

from pulsarity.utils.config import DEFAULT_CONFIG_FILE, PulsarityConfig

if TYPE_CHECKING:
    from pulsarity.events.broker import EventBroker
    from pulsarity.interface.timer_manager import TimerInterfaceManager
    from pulsarity.race.processor import RaceProcessorManager
    from pulsarity.race.state import RaceStateManager
    from pulsarity.webserver._auth import PulsarityUser


loop_ctx: ContextVar[AbstractEventLoop] = ContextVar("loop_ctx")
config_ctx: ContextVar[PulsarityConfig] = ContextVar(
    "config_ctx", default=PulsarityConfig.from_file(DEFAULT_CONFIG_FILE)
)

event_broker_ctx: ContextVar[EventBroker] = ContextVar("event_broker_ctx")
race_state_ctx: ContextVar[RaceStateManager] = ContextVar("race_state_ctx")
race_processor_ctx: ContextVar[RaceProcessorManager] = ContextVar("race_processor_ctx")
interface_manager_ctx: ContextVar[TimerInterfaceManager] = ContextVar(
    "interface_manager_ctx"
)

request_ctx: ContextVar[Request] = ContextVar("request_ctx")
websocket_ctx: ContextVar[WebSocket] = ContextVar("websocket_ctx")
user_ctx: ContextVar[PulsarityUser] = ContextVar("user_ctx")
user_permsissions_ctx: ContextVar[set[str]] = ContextVar("user_permsissions_ctx")
