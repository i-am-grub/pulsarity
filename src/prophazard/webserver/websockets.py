"""
Webserver Websocket Connections
"""

import logging
from asyncio import TaskGroup, CancelledError
from uuid import UUID

from quart import Blueprint, websocket, copy_current_websocket_context
from quart_auth import Unauthorized
from pydantic import BaseModel, UUID4, ValidationError

from .auth import permission_required
from ..database.user import SystemDefaultPerms
from ..database.race._orm.raceformat import RaceSchedule
from ..extensions import current_app, current_user
from ..events import SpecialEvt, RaceSequenceEvt

logger = logging.getLogger(__name__)

websockets = Blueprint("websockets", __name__, url_prefix="/ws")


class EventWSData(BaseModel):
    """
    Class for validating websocket data
    """

    id: UUID4
    event_id: str
    data: dict


async def _get_user_permissions() -> set[str]:
    """
    Gets the permissions for a given UUID

    :raises Unauthorized: _description_
    :return: The set of user permissions
    """
    user_uuid = UUID(hex=current_user.auth_id)
    user_database = await current_app.get_user_database()
    session_maker = user_database.new_session_maker()

    async with session_maker() as session:

        db_user = await user_database.users.get_by_uuid(session, user_uuid)

        if db_user is None:
            raise Unauthorized

        permissions = await db_user.permissions

    return permissions


@websockets.websocket("/server")
@permission_required(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_ws() -> None:
    """
    The primary websocket for the main web application
    """

    @copy_current_websocket_context
    async def server_sending() -> None:

        permissions = await _get_user_permissions()

        async for event in current_app.event_broker.subscribe():
            _, permission, event_id, event_uuid, data = event

            if event_id == SpecialEvt.PERMISSIONS_UPDATE.id:
                permissions = await _get_user_permissions()

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

            current_app.add_background_task(_process_recieved_event_data, model)

    try:
        async with TaskGroup() as tg:
            tg.create_task(server_sending())
            tg.create_task(server_receiving())
    except CancelledError:
        pass


async def _process_recieved_event_data(model: EventWSData) -> None:
    """
    Process data recieved over the event websocket

    :param data: Event data
    """
    # pylint: disable=W0511

    match model.event_id:

        case RaceSequenceEvt.RACE_SCHEDULE.id:
            schedule = RaceSchedule(
                stage_time_sec=3,
                random_stage_delay=0,
                unlimited_time=False,
                race_time_sec=60,
                overtime_sec=0,
            )
            current_app.race_manager.schedule_race(schedule, **model.data)

        case RaceSequenceEvt.RACE_STOP.id:
            current_app.race_manager.stop_race()

        case SpecialEvt.HEARTBEAT.id:
            current_app.event_broker.publish(
                SpecialEvt.HEARTBEAT, model.data, uuid=model.id
            )
