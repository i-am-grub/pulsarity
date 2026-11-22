"""
Webserver Websocket Connections
"""

import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from google.protobuf.message import DecodeError
from starlette.routing import BaseRoute, WebSocketRoute
from starlette.websockets import WebSocketDisconnect

from pulsarity._core import ctx
from pulsarity._core._protobuf import websocket_pb2
from pulsarity._core.database.permission import SystemDefaultPerms
from pulsarity._core.events import client as client_evts
from pulsarity._core.utils import background
from pulsarity._core.webserver._auth import PulsarityWebsocket, requires
from pulsarity._core.webserver._status_codes import WebSocketStatusCodes

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

logger = logging.getLogger(__name__)


class _WebsocketClosureInfo(NamedTuple):
    """
    Websocket closure status and message pairing
    """

    code: WebSocketStatusCodes
    message: str


class _WebsocketClosure(_WebsocketClosureInfo, Enum):
    """
    Enum for different types of websocket closures
    """

    NORMAL_CLOSURE = WebSocketStatusCodes.NORMAL_CLOSURE, "standard client disconnect"
    GOING_AWAY = WebSocketStatusCodes.GOING_AWAY, "server shutting down"
    INTERNAL_ERROR = WebSocketStatusCodes.INTERNAL_ERROR, "internal server error"


async def send_event_data() -> None:
    """
    Handles writing event data over the websocket
    """
    websocket = ctx.websocket_ctx.get()
    permissions = ctx.user_permsissions_ctx.get()

    async for event in ctx.event_broker.subscribe():
        if permissions is None:
            continue

        if event.permission in permissions:
            serialized_message = event.message_dump_protobuf()
            await websocket.send_bytes(serialized_message)


async def simplex_recieve_event_data() -> None:
    """
    Monitors recieved data for an incoming client disconnect message.
    """
    websocket = ctx.websocket_ctx.get()

    while True:
        message = await websocket.receive()

        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message["code"], message.get("reason"))


async def duplex_recieve_event_data() -> None:
    """
    Handles recieved data from the websocket connection.

    Workflow:
    - Parse protocol buffer data
    - Get event handler from registry
    - Check if the user has the required event permissions
    - Use the event handler to validate the data
    - Schedule the event to run as a background task
    """
    websocket = ctx.websocket_ctx.get()
    permissions = ctx.user_permsissions_ctx.get()
    user = websocket.user

    while True:
        data = await websocket.receive_bytes()

        try:
            event = websocket_pb2.WebsocketEvent.FromString(data)
        except DecodeError:
            logger.debug("Error parsing websocket data: %s", data)
            continue

        try:
            evt_cls = client_evts.registry[event.event_id]
        except KeyError:
            logger.exception(
                "%s attempted to route data to non-registered event handler: %s",
                user.identity,
                event,
            )
            continue

        if evt_cls.permission not in permissions:
            logger.warning(
                "%s attempted to activate websocket event with invalid permissions: %s",
                user.identity,
                event,
            )
            continue

        try:
            validated_evt = evt_cls.from_ws_event(event)

        except TypeError, ValueError:
            logger.debug("Error validating websocket data: %s", event)
            continue

        background.add_background_task(validated_evt.run_handler)


async def ws_connection(
    websocket: PulsarityWebsocket,
    rev_coro_func: Callable[[], Coroutine[None, None, None]],
) -> None:
    """
    Websocket client connection.

    Manages seperate tasks for sending event data to and recieving data from
    connected clients

    :param websocket: The client websocket connection
    :param rev_coro_func: The coroutine function to use for handling incoming data
    from the connected client
    """
    close_info = _WebsocketClosure.NORMAL_CLOSURE

    await websocket.accept(headers=[(b"Content-Type", b"application/x-protobuf")])

    websocket_token = ctx.websocket_ctx.set(websocket)
    permission_token = ctx.user_permsissions_ctx.set(websocket.auth.scopes)

    try:
        async with asyncio.TaskGroup() as tg:
            recv_task = tg.create_task(rev_coro_func())
            send_task = tg.create_task(send_event_data())

            await ctx.shutdown_app.wait()

            recv_task.cancel()
            send_task.cancel()

        close_info = _WebsocketClosure.GOING_AWAY

    except* WebSocketDisconnect:
        logger.debug(
            "Client disconnected from websocket (id=%s)",
            websocket.user.identity,
        )

    except* BaseException:
        close_info = _WebsocketClosure.INTERNAL_ERROR
        raise

    finally:
        await websocket.close(*close_info)
        ctx.websocket_ctx.reset(websocket_token)
        ctx.user_permsissions_ctx.reset(permission_token)


@requires(SystemDefaultPerms.READ_WEBSOCKET)
async def simplex_ws(websocket: PulsarityWebsocket):
    """
    The simplex event websocket connection for clients.

    Prevents the ability to generate new websocket connections
    if the server is signalled to shut down.
    """
    if ctx.shutdown_app.is_set():
        await websocket.close(*_WebsocketClosure.GOING_AWAY)
        return

    logger.debug(
        "Establishing simplex websocket connection (id=%s)", websocket.user.identity
    )

    with ctx.ws_conn_tracker:
        await ws_connection(websocket, simplex_recieve_event_data)


@requires((SystemDefaultPerms.READ_WEBSOCKET, SystemDefaultPerms.WRITE_WEBSOCKET))
async def duplex_ws(websocket: PulsarityWebsocket):
    """
    The full duplex event websocket connection for clients

    Prevents the ability to generate new websocket connections
    if the server is signalled to shut down.
    """
    if ctx.shutdown_app.is_set():
        await websocket.close(*_WebsocketClosure.GOING_AWAY)
        return

    logger.debug(
        "Establishing duplex websocket connection (id=%s)", websocket.user.identity
    )

    with ctx.ws_conn_tracker:
        await ws_connection(websocket, duplex_recieve_event_data)


ROUTES: list[BaseRoute] = [
    WebSocketRoute("/ws/simplex", endpoint=simplex_ws),
    WebSocketRoute("/ws/duplex", endpoint=duplex_ws),
]
