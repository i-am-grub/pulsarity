"""
Webserver Websocket Connections
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, NamedTuple, ParamSpec, TypeVar
from uuid import UUID

from google.protobuf.message import DecodeError  # type: ignore
from pydantic import TypeAdapter, ValidationError
from starlette.authentication import requires
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from pulsarity import ctx
from pulsarity._protobuf import websocket_pb2
from pulsarity._validation import websocket as ws_validation
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.events import RaceSequenceEvt, SpecialEvt, _ApplicationEvt
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

ws_shutdown = asyncio.Event()
ws_restart = asyncio.Event()

WS_EVENT_ADAPTER: TypeAdapter[ws_validation.BaseEvent] = TypeAdapter(
    ws_validation.WebsocketEvent
)


class _Route(NamedTuple):
    permission: UserPermission
    func: Callable


_wse_routes: dict[websocket_pb2.EventID, _Route] = {}  # type: ignore


class _ExternalEvent(NamedTuple):
    uuid: UUID
    event_id: websocket_pb2.EventID
    data: dict[str, Any]


def ws_event(event: _ApplicationEvt):
    """
    Decorator for registerting routes based on recieved websocket event data

    :param event: The event to base the routing on
    """
    assert event.event_id not in _wse_routes, (
        "Multiple routes can not be register for a individual application event"
    )

    def inner(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        _wse_routes[event.event_id] = _Route(event.permission, func)
        return func

    return inner


@requires(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_event_ws(websocket: WebSocket):
    """
    The full duplex event websocket connection for clients
    """
    await websocket.accept()

    ctx.websocket_ctx.set(websocket)
    ctx.user_ctx.set(websocket.user)

    permissions = await ctx.user_ctx.get().get_permissions()
    ctx.user_permsissions_ctx.set(permissions)

    try:
        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(_recieve_event_data())
            background.add_pregenerated_task(task)
            await _send_event_data()
    except* WebSocketDisconnect:
        logger.debug("%s disconnected from websocket", ctx.user_ctx.get().display_name)
    finally:
        await websocket.close()


async def _recieve_event_data() -> None:
    """
    Handles recieved data over the websocket
    """
    websocket = ctx.websocket_ctx.get()

    while True:
        data = await websocket.receive_bytes()

        try:
            event = websocket_pb2.WebsocketEvent.FromString(data)
        except DecodeError:
            logger.debug("Error parsing websocket data: %s", data)
            continue

        try:
            event_ = WS_EVENT_ADAPTER.validate_python(event, from_attributes=True)
        except ValidationError:
            logger.debug("Error validating websocket data: %s", event)
        else:
            background.add_background_task(handle_ws_event, event_)


async def _send_event_data() -> None:
    """
    Handles writing event data over the websocket
    """
    event_broker = ctx.event_broker_ctx.get()
    websocket = ctx.websocket_ctx.get()
    user = ctx.user_ctx.get()
    permissions = ctx.user_permsissions_ctx.get()

    async for event in event_broker.subscribe():
        if permissions is None:
            continue

        if event.evt.event_id == SpecialEvt.PERMISSIONS_UPDATE.event_id:
            temp = await user.get_permissions()
            permissions.clear()
            permissions.update(temp)

        elif event.evt.permission in permissions:
            evt = _ExternalEvent(event.uuid, event.evt.event_id, event.data)
            evt_ = WS_EVENT_ADAPTER.validate_python(evt, from_attributes=True)
            data = evt_.model_dump_protobuf()
            await websocket.send_bytes(data)


async def handle_ws_event(event: ws_validation.WebsocketEvent):
    """
    Routes the event data to the proper websocket action while
    ensuring the user has the proper permissions

    :param event: The websocket event
    """
    try:
        route = _wse_routes[event.event_id]
    except KeyError:
        logger.exception(
            "Route not defined for websocket data. Event ID: %s", event.event_id
        )

    if route.permission in ctx.user_permsissions_ctx.get():
        await ensure_async(route.func, event)


@ws_event(SpecialEvt.HEARTBEAT)
async def heatbeat_echo(event: ws_validation.SystemHeartbeat):
    """
    Echo recieved heatbeat data

    :param event: The websocket event data
    """
    event_broker = ctx.event_broker_ctx.get()
    event_broker.publish(SpecialEvt.HEARTBEAT, uuid_=event.uuid)


@ws_event(SpecialEvt.SHUTDOWN)
async def shutdown_server(_event: ws_validation.SystemShutdown):
    """
    Shutdown the webserver
    """
    ws_shutdown.set()


@ws_event(SpecialEvt.RESTART)
async def restart_server(_event: ws_validation.SystemRestart):
    """
    Restart the webserver
    """
    ws_restart.set()


@ws_event(RaceSequenceEvt.RACE_SCHEDULE)
async def schedule_race(_event: ws_validation.ScheduleRace):
    """
    Schedule the start of a race.
    """


@ws_event(RaceSequenceEvt.RACE_STOP)
async def race_stop(_event: ws_validation.RaceStop):
    """
    Stop the current race
    """
    ctx.race_manager_ctx.get().stop_race()


ROUTES = [
    WebSocketRoute("/ws", endpoint=server_event_ws),
]
