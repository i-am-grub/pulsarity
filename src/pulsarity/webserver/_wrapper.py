"""
Endpoint wrappers
"""

from __future__ import annotations

import functools
import inspect
import logging
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeVar, overload

from google.protobuf.message import DecodeError
from pydantic import BaseModel, ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from pulsarity import ctx
from pulsarity._validation import websocket as ws_validation
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver._auth import requires

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Coroutine

    from starlette.requests import Request

    from pulsarity._protobuf import websocket_pb2
    from pulsarity._validation._base import ProtocolBufferModel
    from pulsarity.events import SystemEvt


T = TypeVar("T")
U = TypeVar("U", bound=ws_validation.BaseEvent)

logger = logging.getLogger(__name__)


class _ValModels(NamedTuple):
    request: type[ProtocolBufferModel] | None
    query: type[BaseModel] | None
    path: type[BaseModel] | None


class _Route(NamedTuple):
    permission: UserPermission
    func: Callable


class ProtobufResponse(Response):
    """
    Response sending protocol buffer data
    """

    # pylint: disable=R0913,R0917

    __slots__ = ("background", "body", "status_code")

    media_type = "application/x-protobuf"

    def __init__(
        self,
        content: ProtocolBufferModel,
        status_code=200,
        headers=None,
        media_type=None,
        background=None,
    ):
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: ProtocolBufferModel) -> bytes:
        return content.model_dump_protobuf().SerializeToString()


def endpoint(
    *permissions: UserPermission,
    requires_auth: bool = True,
    request_model: type[ProtocolBufferModel] | None = None,
    query_model: type[BaseModel] | None = None,
    path_model: type[BaseModel] | None = None,
):
    """
    Decorator for validating request data, user permissions, and
    response data for a route

    :param permission: The permissions required to access the route
    :param requires_auth: Whether the endpoint request authentication or nots, defaults to True
    :param request_model: The model to use to validate the request, defaults to None
    :param query_model: The adapter model to use to validate the query parameters, defaults to None
    :param path_model: The adapter model to use to validate the query parameters, defaults to None
    """

    def inner(
        func: Callable[..., ProtocolBufferModel | Response],
    ) -> Callable[[Request], Coroutine[None, None, Response]]:
        # pylint: disable=R0912

        base_kwargs = {"request", "query", "path"}
        function_kwargs = set(inspect.signature(func).parameters.keys())

        if not function_kwargs.issubset(base_kwargs):
            msg = (
                f"{func.__name__} uses incompatible argument names. "
                f"Arguments must be limited to {base_kwargs}"
            )
            raise KeyError(msg)

        for perm in permissions:
            if not isinstance(perm, UserPermission):
                msg = f"{perm} is not a valid {UserPermission.__name__}"
                raise TypeError(msg)

        _validate_compatibility(func, request_model, function_kwargs, "request")
        _validate_compatibility(func, query_model, function_kwargs, "query")
        _validate_compatibility(func, path_model, function_kwargs, "path")

        models = _ValModels(request_model, query_model, path_model)

        if requires_auth:

            @functools.wraps(func)
            @requires(SystemDefaultPerms.AUTHENTICATED, status_code=401)
            @requires(permissions, status_code=403)
            async def wrapper(request: Request) -> Response:
                with ctx.request_ctx.set(request), ctx.user_ctx.set(request.user):  # type: ignore
                    return await _process_request(func, request, models)

        else:

            @functools.wraps(func)
            async def wrapper(request: Request) -> Response:
                with ctx.request_ctx.set(request), ctx.user_ctx.set(request.user):  # type: ignore
                    return await _process_request(func, request, models)

        return wrapper

    return inner


def _validate_compatibility(
    func: Callable, model: type[BaseModel] | None, used_kwargs: set[str], arg_id: str
):
    """
    Validate the compatibility between the function and provided model
    """

    if model is not None:
        if arg_id not in used_kwargs:
            msg = (
                f"'{arg_id}` must be an argument of the endpoint function "
                "when a request model has been provided"
            )
            raise KeyError(msg)

        if not issubclass(model, BaseModel):
            msg = (
                f"{func.__name__} query model is not a subclass of {BaseModel.__name__}"
            )
            raise ValueError(msg)

    elif arg_id in used_kwargs:
        msg = (
            f"'{arg_id}` must NOT be an argument of the endpoint "
            f"function when a {arg_id} model has NOT been provided"
        )
        raise KeyError(msg)


async def _process_request(
    func: Callable, request: Request, val_models: _ValModels
) -> Response:
    """
    Processes the incoming request
    """
    kwargs: dict[str, BaseModel] = {}

    if val_models.request is not None:
        content_type = request.headers.get("content-type")
        if content_type != "application/x-protobuf":
            raise HTTPException(status_code=415)

        try:
            data = await request.body()
            kwargs["request"] = val_models.request.model_validate_protobuf(data)
        except DecodeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValidationError as ex:
            raise HTTPException(status_code=422) from ex

    if val_models.query is not None:
        try:
            kwargs["query"] = val_models.query.model_validate(request.query_params)
        except JSONDecodeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValidationError as ex:
            raise HTTPException(status_code=422) from ex

    if val_models.path is not None:
        try:
            kwargs["path"] = val_models.path.model_validate(request.path_params)
        except JSONDecodeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValidationError as ex:
            raise HTTPException(status_code=422) from ex

    try:
        endpoint_result = await ensure_async(func, **kwargs)
    except ValidationError as ex:
        raise HTTPException(status_code=500) from ex

    if isinstance(endpoint_result, Response):
        return endpoint_result

    return Response()


_wse_routes: dict[websocket_pb2.EventID, _Route] = {}


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


@overload
def ws_event(
    evt: Literal[SystemEvt.HEARTBEAT],
) -> Callable[
    [Callable[[ws_validation.SystemHeartbeat], Awaitable[T]]],
    Callable[[ws_validation.SystemHeartbeat], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.SHUTDOWN],
) -> Callable[
    [Callable[[ws_validation.SystemShutdown], Awaitable[T]]],
    Callable[[ws_validation.SystemShutdown], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.RESTART],
) -> Callable[
    [Callable[[ws_validation.SystemRestart], Awaitable[T]]],
    Callable[[ws_validation.SystemRestart], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.RACE_SCHEDULE],
) -> Callable[
    [Callable[[ws_validation.ScheduleRace], Awaitable[T]]],
    Callable[[ws_validation.ScheduleRace], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.RACE_STOP],
) -> Callable[
    [Callable[[ws_validation.RaceStop], Awaitable[T]]],
    Callable[[ws_validation.RaceStop], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.PILOT_ADD],
) -> Callable[
    [Callable[[ws_validation.PilotAddEvent], Awaitable[T]]],
    Callable[[ws_validation.PilotAddEvent], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.PILOT_ALTER],
) -> Callable[
    [Callable[[ws_validation.PilotAlterEvent], Awaitable[T]]],
    Callable[[ws_validation.PilotAlterEvent], Awaitable[T]],
]: ...
@overload
def ws_event(
    evt: Literal[SystemEvt.PILOT_DELETE],
) -> Callable[
    [Callable[[ws_validation.PilotDeleteEvent], Awaitable[T]]],
    Callable[[ws_validation.PilotDeleteEvent], Awaitable[T]],
]: ...
def ws_event(
    evt: SystemEvt,
) -> Callable[[Callable[[U], Awaitable[T]]], Callable[[U], Awaitable[T]]]:
    """
    Decorator for registerting routes based on recieved websocket event data

    :param event: The event to base the routing on
    """
    if evt.event_id in _wse_routes:
        msg = "Multiple routes can not be register for a individual application event"
        raise RuntimeError(msg)

    def inner(
        func: Callable[[U], Awaitable[T]],
    ) -> Callable[[U], Awaitable[T]]:
        _wse_routes[evt.event_id] = _Route(evt.permission, func)
        return func

    return inner
