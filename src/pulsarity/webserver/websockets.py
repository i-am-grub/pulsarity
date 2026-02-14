"""
Webserver Websocket Connections
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from google.protobuf.message import DecodeError  # type: ignore
from pydantic import TypeAdapter, ValidationError
from starlette.authentication import requires
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from pulsarity import ctx
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.events import RaceSequenceEvt, SpecialEvt, _ApplicationEvt
from pulsarity.protobuf import websocket_pb2
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver import validation

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

ws_shutdown = asyncio.Event()
ws_restart = asyncio.Event()

_wse_routes: dict[websocket_pb2.EventID, tuple[UserPermission, Callable]] = {}  # type: ignore


WS_EVENT_ADAPTER = TypeAdapter(validation.WebsocketEvent)  # type: ignore


def ws_event(event: _ApplicationEvt):
    """
    Decorator to route recieved websocket event data

    :param event: The event to base the routing on
    """

    def inner(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        _wse_routes[event.event_id] = (event.permission, func)

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
            task = tg.create_task(_recieve_data())
            background.add_pregenerated_task(task)
            await _write_data()
    except* WebSocketDisconnect:
        logger.debug("%s disconnected from websocket", ctx.user_ctx.get().display_name)
    finally:
        await websocket.close()


async def _recieve_data() -> None:
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


async def _write_data() -> None:
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
            evt_message = websocket_pb2.WebsocketEvent()
            evt_message.id = event.uuid.bytes
            evt_message.event_id = event.evt.event_id
            await websocket.send_bytes(evt_message.SerializeToString())


async def handle_ws_event(event: validation.WebsocketEvent):
    """
    Handle the event identified in the websocket data while enforcing
    the its permissions

    :param ws_data: The recieved websocket data
    :param permissions: The permissions for the user
    """

    if event.event_id in _wse_routes:
        permission, route = _wse_routes[event.event_id]

        if permission in ctx.user_permsissions_ctx.get():
            await ensure_async(route, event)

    else:
        logger.debug("Route not available for websocket data")


@ws_event(SpecialEvt.HEARTBEAT)
async def heatbeat_echo(event: validation.WebsocketEvent):
    """
    Echo recieved heatbeat data

    :param ws_data: Recieved websocket event data
    """
    event_broker = ctx.event_broker_ctx.get()
    event_broker.publish(SpecialEvt.HEARTBEAT, ws_data.data, uuid_=ws_data.id)


@ws_event(SpecialEvt.SHUTDOWN)
async def shutdown_server(event: validation.WebsocketEvent):
    """
    Shutdown the webserver
    """
    ws_shutdown.set()


@ws_event(SpecialEvt.RESTART)
async def restart_server(event: validation.WebsocketEvent):
    """
    Restart the webserver
    """
    ws_restart.set()


@ws_event(RaceSequenceEvt.RACE_SCHEDULE)
async def schedule_race(event: validation.WebsocketEvent):
    """
    Schedule the start of a race.
    """


@ws_event(RaceSequenceEvt.RACE_STOP)
async def race_stop(event: validation.WebsocketEvent):
    """
    Stop the current race
    """
    ctx.race_manager_ctx.get().stop_race()


ROUTES = [
    WebSocketRoute("/ws", endpoint=server_event_ws),
]
