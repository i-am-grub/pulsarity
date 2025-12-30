"""
Webserver Components
"""

import asyncio
import logging
from secrets import token_urlsafe
from typing import TypedDict

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from pulsarity import ctx
from pulsarity.events import EventBroker
from pulsarity.interface.timer_manager import TimerInterfaceManager
from pulsarity.race.processor import RaceProcessorManager
from pulsarity.race.state import RaceStateManager
from pulsarity.webserver._auth import PulsarityAuthBackend
from pulsarity.webserver.routes import ROUTES as http_routes
from pulsarity.webserver.websockets import ROUTES as ws_routes

logger = logging.getLogger(__name__)


class ContextState(TypedDict):
    """
    Context payload
    """

    loop: asyncio.AbstractEventLoop
    event: EventBroker
    race_state: RaceStateManager
    race_processor: RaceProcessorManager
    timer_inferface_manager: TimerInterfaceManager


class PulsarityContextMiddleware:
    """
    Middleware for propagating context into the application
    """

    # pylint: disable=R0903

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        state: ContextState = scope["state"]
        loop_token = ctx.loop_ctx.set(state["loop"])
        event_token = ctx.event_broker_ctx.set(state["event"])
        race_state_token = ctx.race_state_ctx.set(state["race_state"])
        race_processor_token = ctx.race_processor_ctx.set(state["race_processor"])
        timer_interface_token = ctx.interface_manager_ctx.set(
            state["timer_inferface_manager"]
        )

        try:
            await self.app(scope, receive, send)

        finally:
            ctx.loop_ctx.reset(loop_token)
            ctx.event_broker_ctx.reset(event_token)
            ctx.race_state_ctx.reset(race_state_token)
            ctx.race_processor_ctx.reset(race_processor_token)
            ctx.interface_manager_ctx.reset(timer_interface_token)


class SPAStaticFiles(StaticFiles):
    """
    Staticfiles for single-page-apps

    Wraps the base `lookup_path` to fallback to the root `index.html`.
    """

    def lookup_path(self, path):
        full_path, stat_result = super().lookup_path(path)
        if stat_result is None:
            return super().lookup_path("./index.html")

        return full_path, stat_result


def generate_application() -> Starlette:
    """
    Generates the Pulsarity application

    :return: The starlette application object
    """
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
        ),
        Middleware(
            SessionMiddleware,
            store=CookieStore(secret_key=token_urlsafe(32)),
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(AuthenticationMiddleware, backend=PulsarityAuthBackend()),
    ]

    return Starlette(
        routes=http_routes + ws_routes,  # type: ignore
        lifespan=None,
        middleware=middleware,
    )
