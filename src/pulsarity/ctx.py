"""
Application context managment
"""

from asyncio import AbstractEventLoop
from contextvars import ContextVar
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.websockets import WebSocket

if TYPE_CHECKING:
    from pulsarity.webserver.auth import PulsarityUser

loop_ctx: ContextVar[AbstractEventLoop] = ContextVar("loop_ctx")
request_ctx: ContextVar[Request] = ContextVar("request_ctx")
websocket_ctx: ContextVar[WebSocket] = ContextVar("websocket_ctx")
user_ctx: ContextVar["PulsarityUser"] = ContextVar("user_ctx")
