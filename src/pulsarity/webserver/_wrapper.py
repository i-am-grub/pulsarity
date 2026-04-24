"""
Endpoint wrappers
"""

from __future__ import annotations

import functools
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Self,
    TypeVar,
    dataclass_transform,
)

from google.protobuf.message import DecodeError, Message
from starlette.exceptions import HTTPException
from starlette.responses import Response

from pulsarity import ctx
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver._auth import requires

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from starlette.requests import Request


T = TypeVar("T")


logger = logging.getLogger(__name__)


class ProtobufResponse(Response):
    """
    Response sending protocol buffer data
    """

    # pylint: disable=R0913,R0917

    __slots__ = ("background", "body", "status_code")

    media_type = "application/x-protobuf"

    def __init__(
        self,
        content: Message,
        status_code=200,
        headers=None,
        media_type=None,
        background=None,
    ):
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: Message) -> bytes:
        return content.SerializeToString()


@dataclass(slots=True)
class _HttpModel:
    """
    Base class for http route data

    When data is being validated with `__post_init__`, validation errors
    should raise `ValueError`
    """


@dataclass_transform()
def http_route_dataclass(cls: type[_HttpModel]) -> type[_HttpModel]:
    return dataclass(cls, slots=True)


@http_route_dataclass
class QueryDataModel(_HttpModel):
    """
    Dataclass for query parameter data
    """


@http_route_dataclass
class PathDataModel(_HttpModel):
    """
    Dataclass for request path data
    """


@http_route_dataclass
class RequestModel(_HttpModel, ABC):
    """
    Dataclass for post/put request data
    """

    @classmethod
    @abstractmethod
    def from_protobuf(cls, data: bytes) -> Self:
        """
        Generate a request instance from recieved bytes
        """


class _ValModels(NamedTuple):
    request: type[RequestModel] | None
    query: type[QueryDataModel] | None
    path: type[PathDataModel] | None


def endpoint(
    *permissions: UserPermission,
    requires_auth: bool = True,
    request_model: type[RequestModel] | None = None,
    query_model: type[QueryDataModel] | None = None,
    path_model: type[PathDataModel] | None = None,
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
        func: Callable[..., Response],
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
                with ctx.request_ctx.set(request), ctx.user_ctx.set(request.user):
                    return await _process_request(func, request, models)

        else:

            @functools.wraps(func)
            async def wrapper(request: Request) -> Response:
                with ctx.request_ctx.set(request), ctx.user_ctx.set(request.user):
                    return await _process_request(func, request, models)

        return wrapper

    return inner


def _validate_compatibility(
    func: Callable, model: type[_HttpModel] | None, used_kwargs: set[str], arg_id: str
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

        if not issubclass(model, _HttpModel):
            msg = f"{func.__name__} query model is not a subclass of {_HttpModel.__name__}"
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
    kwargs: dict[str, _HttpModel] = {}

    if val_models.request is not None:
        content_type = request.headers.get("content-type")
        if content_type != "application/x-protobuf":
            raise HTTPException(status_code=415)

        try:
            data = await request.body()
            kwargs["request"] = val_models.request.from_protobuf(data)
        except DecodeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValueError as ex:
            raise HTTPException(status_code=422) from ex

    if val_models.query is not None:
        try:
            kwargs["query"] = val_models.query(**request.query_params)
        except TypeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValueError as ex:
            raise HTTPException(status_code=422) from ex

    if val_models.path is not None:
        try:
            kwargs["path"] = val_models.path(**request.path_params)
        except TypeError as ex:
            raise HTTPException(status_code=400) from ex
        except ValueError as ex:
            raise HTTPException(status_code=422) from ex

    try:
        endpoint_result = await ensure_async(func, **kwargs)
    except ValueError as ex:
        raise HTTPException(status_code=500) from ex

    if isinstance(endpoint_result, Response):
        return endpoint_result

    return Response()
