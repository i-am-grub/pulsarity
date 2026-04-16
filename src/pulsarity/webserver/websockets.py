"""
Webserver Websocket Connections
"""

import asyncio
import logging
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from google.protobuf.message import DecodeError
from starlette.authentication import requires
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from pulsarity import ctx
from pulsarity._protobuf import websocket_pb2
from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.events import client
from pulsarity.utils import background

if TYPE_CHECKING:
    from pulsarity.webserver._auth import PulsarityUser

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)


@requires(SystemDefaultPerms.EVENT_WEBSOCKET)
async def server_event_ws(websocket: WebSocket):
    """
    The full duplex event websocket connection for clients
    """
    await websocket.accept()

    user: PulsarityUser = websocket.user
    permissions = await user.get_permissions()

    websocket_token = ctx.websocket_ctx.set(websocket)
    user_token = ctx.user_ctx.set(user)
    permission_token = ctx.user_permsissions_ctx.set(permissions)

    try:
        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(_recieve_event_data())
            background.add_pregenerated_task(task)
            await _send_event_data()

    except* WebSocketDisconnect:
        logger.debug("%s disconnected from websocket", ctx.user_ctx.get().display_name)

    finally:
        ctx.websocket_ctx.reset(websocket_token)
        ctx.user_ctx.reset(user_token)
        ctx.user_permsissions_ctx.reset(permission_token)
        await websocket.close()


async def _recieve_event_data() -> None:
    """
    Handles recieved data over the websocket
    """
    websocket = ctx.websocket_ctx.get()
    user = ctx.user_ctx.get()

    while True:
        data = await websocket.receive_bytes()

        try:
            event = websocket_pb2.WebsocketEvent.FromString(data)
        except DecodeError:
            logger.debug("Error parsing websocket data: %s", data)
            continue

        try:
            cls = client.registry[event.event_id]
        except KeyError:
            logger.exception(
                "Attempted to route data to non-registed event handler: %s", event
            )
            continue

        if not user.has_permission(cls.permission):
            logger.debug("User does not have permission for event: %s", event)
            continue

        try:
            parsed_evt = cls.from_ws_event(event)

        except TypeError, ValueError:
            logger.debug("Error validating websocket data: %s", event)

        else:
            background.add_background_task(parsed_evt.run_handler)


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

        if event.event_id == websocket_pb2.EVENT_PERMISSIONS_UPDATE:
            temp = await user.get_permissions()
            permissions.clear()
            permissions.update(temp)
            await websocket.send_bytes(event.model_dump_protobuf())

        elif event.permission in permissions:
            await websocket.send_bytes(event.model_dump_protobuf())


ROUTES = [
    WebSocketRoute("/ws", endpoint=server_event_ws),
]
