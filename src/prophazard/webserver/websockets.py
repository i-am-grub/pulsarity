"""
Webserver Websocket Connections
"""

import os
import signal
import logging
import asyncio
from typing import TypeVar, ParamSpec
from collections.abc import Callable, Awaitable

from quart import Blueprint, websocket, copy_current_websocket_context
from pydantic import BaseModel, UUID4, ValidationError

from .auth import permission_required
from ..database.user import SystemDefaultPerms, UserPermission
from ..database.race._orm.raceformat import RaceSchedule
from ..extensions import current_app, current_user
from ..events import _ApplicationEvt, SpecialEvt, RaceSequenceEvt

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

websockets = Blueprint("websockets", __name__, url_prefix="/ws")

_routes: dict[str, tuple[UserPermission, Callable]] = {}


class EventWSData(BaseModel):
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

        _routes[event.id] = (event.permission, func)

        return func

    return inner


async def handle_ws_event(ws_data: EventWSData, permissions: set[str]):
    """
    Handle the event identified in the websocket data

    :param ws_data: The recieved websocket data
    :param permissions: The permissions for the user
    """

    if ws_data.event_id in _routes:
        permission, route = _routes[ws_data.event_id]

        if permission in permissions:
            await route(ws_data)

    else:
        logger.debug("Route not available for websocket data")


@websockets.websocket("/server")
@permission_required(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_ws() -> None:
    """
    The primary websocket for the main web application
    """

    @copy_current_websocket_context
    async def server_sending() -> None:

        async for event in current_app.event_broker.subscribe():
            _, permission, event_id, event_uuid, data = event

            if event_id == SpecialEvt.PERMISSIONS_UPDATE.id:
                temp = await current_user.get_permissions()
                permissions.clear()
                permissions.update(temp)

            elif permission in permissions:
                evt_data = EventWSData(id=event_uuid, event_id=event_id, data=data)
                await websocket.send_json(evt_data.model_dump())

    @copy_current_websocket_context
    async def server_receiving() -> None:
        while True:
            data = await websocket.receive()

            try:
                model = EventWSData.model_validate_json(data)
            except ValidationError:
                logger.debug("Error validating websocket data: %s", data)
                continue

            current_app.add_background_task(handle_ws_event, model, permissions)

    permissions = await current_user.get_permissions()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server_sending())
        tg.create_task(server_receiving())


@ws_event(SpecialEvt.HEARTBEAT)
async def heatbeat_echo(ws_data: EventWSData):
    """
    Echo recieved heatbeat data,

    :param ws_data: Recieved websocket event data
    """
    current_app.event_broker.publish(
        SpecialEvt.HEARTBEAT, ws_data.data, uuid=ws_data.id
    )


@ws_event(SpecialEvt.RESTART)
async def restart_server(_ws_data: EventWSData):
    """
    Restart the webserver

    :param _ws_data: Recieved websocket event data
    """
    os.environ["REBOOT_PH_FLAG"] = "active"
    signal.raise_signal(signal.Signals.SIGTERM)


@ws_event(RaceSequenceEvt.RACE_SCHEDULE)
async def schedule_race(ws_data: EventWSData):
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
    current_app.race_manager.schedule_race(schedule, **ws_data.data)


@ws_event(RaceSequenceEvt.RACE_STOP)
async def race_stop(_ws_data: EventWSData):
    """
    Stop the current race

    :param _ws_data: Recieved websocket event data
    """
    current_app.race_manager.stop_race()
