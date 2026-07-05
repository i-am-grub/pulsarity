"""
Webserver Websocket Connections
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Coroutine

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


logger = logging.getLogger(__name__)

ws_shutdown_evt = asyncio.Event()


class _WebSocketConnTracker:
    """
    Context manager for tracking the client websocket
    connections actively connected to the server
    """

    __slots__ = ("_evt", "_num_conn")

    def __init__(self) -> None:
        self._evt = asyncio.Event()
        self._evt.set()
        self._num_conn = 0

    def __enter__(self):
        self._num_conn += 1
        self._evt.clear()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._num_conn -= 1
        if not self._num_conn:
            self._evt.set()

    async def wait_all_closed(self) -> None:
        """
        Wait for all websocket connections to close
        """
        await self._evt.wait()


conn_tracker = _WebSocketConnTracker()


async def send_event_data() -> None:
    """
    Handles writing event data over the websocket
    """
    event_broker = ctx.event_broker_ctx.get()
    websocket = ctx.websocket_ctx.get()
    permissions = ctx.user_permsissions_ctx.get()

    async for event in event_broker.subscribe():
        if permissions is None:
            continue

        if event.permission in permissions:
            await websocket.send_bytes(event.model_dump_protobuf())


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
    user = ctx.user_ctx.get()
    websocket = ctx.websocket_ctx.get()
    permissions: set[str] = websocket.auth.scopes

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
                "User (%s) attempted to route data to non-registed event handler: %s",
                user.identity,
                event,
            )
            continue

        if cls.permission not in permissions:
            logger.debug(
                "User (%s) does not have permissions for activating event: %s",
                user.identity,
                event,
            )
            continue

        try:
            validated_evt = cls.from_ws_event(event)

        except TypeError, ValueError:
            logger.debug("Error validating websocket data: %s", event)
            continue

        background.add_background_task(validated_evt.run_handler)


async def ws_connection(
    websocket: WebSocket, rev_coro_func: Callable[[], Coroutine[None, None, None]]
) -> None:
    """
    Websocket client connection.

    Manages seperate tasks for sending event data to and recieving data from
    connected clients

    :param websocket: The client websocket connection
    :param rev_coro_func: The coroutine function to use for handling incoming data
    from the connected client
    """
    close_info = 1000, "standard client disconnect"

    await websocket.accept(headers=[(b"Content-Type", b"application/x-protobuf")])

    user: PulsarityUser = websocket.user
    permissions = websocket.auth.scopes

    websocket_token = ctx.websocket_ctx.set(websocket)
    user_token = ctx.user_ctx.set(user)
    permission_token = ctx.user_permsissions_ctx.set(permissions)

    try:
        async with asyncio.TaskGroup() as tg:
            recv_task = tg.create_task(rev_coro_func())
            send_task = tg.create_task(send_event_data())

            await ws_shutdown_evt.wait()

            recv_task.cancel()
            send_task.cancel()

        close_info = 1001, "server shutting down"

    except* WebSocketDisconnect:
        logger.debug(
            "Client disconnected from websocket (id=%s)", ctx.user_ctx.get().identity
        )

    except* BaseException:
        close_info = 1011, "internal server error"
        raise

    finally:
        await websocket.close(*close_info)
        ctx.websocket_ctx.reset(websocket_token)
        ctx.user_ctx.reset(user_token)
        ctx.user_permsissions_ctx.reset(permission_token)


@requires(SystemDefaultPerms.SIMPLEX_WEBSOCKET)
async def simplex_ws(websocket: WebSocket):
    """
    The simplex event websocket connection for clients.

    Prevents the ability to generate new websocket connections
    if the server is signalled to shut down.
    """
    if ws_shutdown_evt.is_set():
        await websocket.close(1001, "server shutting down")
        return

    user: PulsarityUser = websocket.user

    logger.debug("Establishing simplex websocket connection (id=%s)", user.identity)

    with conn_tracker:
        await ws_connection(websocket, simplex_recieve_event_data)


@requires(SystemDefaultPerms.DUPLEX_WEBSOCKET)
async def duplex_ws(websocket: WebSocket):
    """
    The full duplex event websocket connection for clients

    Prevents the ability to generate new websocket connections
    if the server is signalled to shut down.
    """
    if ws_shutdown_evt.is_set():
        await websocket.close(1001, "server shutting down")
        return

    user: PulsarityUser = websocket.user

    logger.debug("Establishing duplex websocket connection (id=%s)", user.identity)

    with conn_tracker:
        await ws_connection(websocket, duplex_recieve_event_data)


ROUTES = [
    WebSocketRoute("/ws/simplex", endpoint=simplex_ws),
    WebSocketRoute("/ws/duplex", endpoint=duplex_ws),
]
