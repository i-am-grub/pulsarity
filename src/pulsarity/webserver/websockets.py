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
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.database.raceformat import RaceSchedule
from pulsarity.events import RaceSequenceEvt, SpecialEvt, _ApplicationEvt, event_broker
from pulsarity.race import race_manager
from pulsarity.utils import background
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver.auth import PulsarityUser

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


async def handle_ws_event(ws_data: WSEventData, permissions: set[str]):
    """
    Handle the event identified in the websocket data while enforcing
    the its permissions

    :param ws_data: The recieved websocket data
    :param permissions: The permissions for the user
    """

    if ws_data.event_id in _wse_routes:
        permission, route = _wse_routes[ws_data.event_id]

        if permission in permissions:
            signature = inspect.signature(route)
            if "ws_data" in signature.parameters:
                await ensure_async(route, ws_data)
            else:
                await ensure_async(route)

    else:
        logger.debug("Route not available for websocket data")


@requires(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_event_ws(websocket: WebSocket):
    """
    The full duplex websocket connection for clients
    """
    ctx.websocket_ctx.set(websocket)

    async def recieve_data() -> None:
        while True:
            data = await websocket.receive_json()

            try:
                model = WSEventData.model_validate(data)
            except ValidationError:
                logger.debug("Error validating websocket data: %s", data)
            else:
                background.add_background_task(handle_ws_event, model, permissions)

    async def write_data() -> None:
        async for event in event_broker.subscribe():
            _, permission, event_id, event_uuid, data = event

            if permissions is None:
                continue

            if event_id == SpecialEvt.PERMISSIONS_UPDATE.id:
                user: PulsarityUser = websocket.user
                temp = await user.get_permissions()

                permissions.clear()
                permissions.update(temp)

            elif permission in permissions:
                evt_data = WSEventData(id=event_uuid, event_id=event_id, data=data)
                await websocket.send_text(evt_data.model_dump_json())

    user: PulsarityUser = websocket.user
    permissions = await user.get_permissions()
    await websocket.accept()

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(recieve_data())
            tg.create_task(write_data())
    except* WebSocketDisconnect:
        ...
    finally:
        await websocket.close()


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
    schedule = RaceSchedule(
        stage_time_sec=3,
        random_stage_delay=0,
        unlimited_time=False,
        race_time_sec=60,
        overtime_sec=0,
    )
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
