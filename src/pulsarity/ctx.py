"""
Application context managment
"""

from asyncio import AbstractEventLoop
from contextvars import ContextVar

from starlette.websockets import WebSocket

loop_ctx: ContextVar[AbstractEventLoop] = ContextVar("loop_ctx")
websocket_ctx: ContextVar[WebSocket] = ContextVar("websocket_ctx")
