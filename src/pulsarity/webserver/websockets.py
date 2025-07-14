"""
Webserver Websocket Connections
"""

import asyncio
import inspect
import logging
import os
import signal
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from pydantic import UUID4, BaseModel, ValidationError
from starlette.authentication import requires
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from pulsarity import ctx
from pulsarity.database import RaceFormat
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.events import RaceSequenceEvt, SpecialEvt, _ApplicationEvt, event_broker
from pulsarity.race import race_manager
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

_wse_routes: dict[str, tuple[UserPermission, Callable]] = {}


class WSEventData(BaseModel):
    """
    Class for validating websocket data
    """

    id: UUID4
    event_id: str
    data: dict


def ws_event(event: _ApplicationEvt):
    """
    Decorator to route recieved websocket event data

    :param event: The event to base the routing on
    """

    def inner(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        _wse_routes[event.id] = (event.permission, func)

        return func

    return inner


@requires(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_event_ws(websocket: WebSocket):
    """
    The full duplex websocket connection for clients
    """
    await websocket.accept()

    ctx.websocket_ctx.set(websocket)
    ctx.user_ctx.set(websocket.user)

    permissions = await ctx.user_ctx.get().get_permissions()
    ctx.user_permsissions_ctx.set(permissions)

    try:
        async with asyncio.TaskGroup() as tg:
            background.add_pregenerated_task(tg.create_task(_recieve_data()))
            background.add_pregenerated_task(tg.create_task(_write_data()))
    except* WebSocketDisconnect:
        ...
    finally:
        await websocket.close()


async def _recieve_data() -> None:
    """
    Handles recieved data over the websocket
    """
    websocket = ctx.websocket_ctx.get()
    while True:
        data = await websocket.receive_json()

        try:
            model = WSEventData.model_validate(data)
        except ValidationError:
            logger.debug("Error validating websocket data: %s", data)
        else:
            background.add_background_task(handle_ws_event, model)


async def _write_data() -> None:
    """
    Handles writing event data over the websocket
    """
    websocket = ctx.websocket_ctx.get()
    user = ctx.user_ctx.get()
    permissions = ctx.user_permsissions_ctx.get()

    async for event in event_broker.subscribe():
        if permissions is None:
            continue

        if event.evt.id == SpecialEvt.PERMISSIONS_UPDATE.id:
            temp = await user.get_permissions()

            permissions.clear()
            permissions.update(temp)

        elif event.evt.permission in permissions:
            evt_data = WSEventData(
                id=event.uuid, event_id=event.evt.id, data=event.data
            )
            await websocket.send_text(evt_data.model_dump_json())


async def handle_ws_event(ws_data: WSEventData):
    """
    Handle the event identified in the websocket data while enforcing
    the its permissions

    :param ws_data: The recieved websocket data
    :param permissions: The permissions for the user
    """

    if ws_data.event_id in _wse_routes:
        permission, route = _wse_routes[ws_data.event_id]

        if permission in ctx.user_permsissions_ctx.get():
            signature = inspect.signature(route)
            if "ws_data" in signature.parameters:
                await ensure_async(route, ws_data)
            else:
                await ensure_async(route)

    else:
        logger.debug("Route not available for websocket data")


@ws_event(SpecialEvt.HEARTBEAT)
async def heatbeat_echo(ws_data: WSEventData):
    """
    Echo recieved heatbeat data

    :param ws_data: Recieved websocket event data
    """
    event_broker.publish(SpecialEvt.HEARTBEAT, ws_data.data, uuid_=ws_data.id)


@ws_event(SpecialEvt.SHUTDOWN)
async def shutdown_server():
    """
    Shutdown the webserver
    """
    signal.raise_signal(signal.Signals.SIGINT)


@ws_event(SpecialEvt.RESTART)
async def restart_server():
    """
    Restart the webserver
    """
    os.environ["REBOOT_PULSARITY_FLAG"] = "active"
    signal.raise_signal(signal.Signals.SIGINT)


@ws_event(RaceSequenceEvt.RACE_SCHEDULE)
async def schedule_race(ws_data: WSEventData):
    """
    Schedule the start of a race.

    :param ws_data: Recieved websocket event data
    """
    schedule = RaceFormat("temp")
    race_manager.schedule_race(schedule, **ws_data.data)


@ws_event(RaceSequenceEvt.RACE_STOP)
async def race_stop():
    """
    Stop the current race

    :param _ws_data: Recieved websocket event data
    """
    race_manager.stop_race()


routes = [
    WebSocketRoute("/server", endpoint=server_event_ws),
]
