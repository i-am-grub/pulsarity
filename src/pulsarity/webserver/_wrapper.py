"""
Endpoint wrappers
"""

import functools
import inspect
import logging
from collections.abc import Callable, Coroutine
from json.decoder import JSONDecodeError
from typing import NamedTuple

from google.protobuf.message import DecodeError  # type: ignore
from pydantic import BaseModel, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from pulsarity import ctx
from pulsarity._validation._base import ProtocolBufferModel
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver._auth import requires

logger = logging.getLogger(__name__)


class _ValModels(NamedTuple):
    request: type[ProtocolBufferModel] | None
    query: type[BaseModel] | None
    path: type[BaseModel] | None


class ProtobufResponse(Response):
    """
    Response sending protocol buffer data
    """

    # pylint: disable=R0913,R0917

    __slots__ = ("status_code", "background", "body")

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

        try:
            assert function_kwargs.issubset(base_kwargs)
        except AssertionError as ex:
            raise KeyError(
                f"{func.__name__} uses incompatible argument names. "
                f"Arguments must be limited to {base_kwargs}"
            ) from ex

        for perm in permissions:
            try:
                assert isinstance(perm, UserPermission)
            except AssertionError as ex:
                raise ValueError(
                    f"{perm} is not a valid {UserPermission.__name__}"
                ) from ex

        _validate_compatibility(func, request_model, function_kwargs, "request")
        _validate_compatibility(func, query_model, function_kwargs, "query")
        _validate_compatibility(func, path_model, function_kwargs, "path")

        models = _ValModels(request_model, query_model, path_model)

        if requires_auth:

            @functools.wraps(func)
            @requires(SystemDefaultPerms.AUTHENTICATED, status_code=401)
            @requires(permissions, status_code=403)
            async def wrapper(request: Request) -> Response:
                return await _process_request(func, request, models)

        else:

            @functools.wraps(func)
            async def wrapper(request: Request) -> Response:
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
        try:
            assert arg_id in used_kwargs
        except AssertionError as ex:
            raise KeyError(
                f"'{arg_id}` must be an argument of the endpoint function "
                "when a request model has been provided"
            ) from ex

        try:
            assert issubclass(model, BaseModel)
        except AssertionError as ex:
            raise ValueError(
                f"{func.__name__} query model is not a subclass of {BaseModel.__name__}"
            ) from ex
    else:
        try:
            assert arg_id not in used_kwargs
        except AssertionError as ex:
            raise KeyError(
                f"'{arg_id}` must NOT be an argument of the endpoint "
                f"function when a {arg_id} model has NOT been provided"
            ) from ex


async def _process_request(
    func: Callable, request: Request, val_models: _ValModels
) -> Response:
    """
    Processes the incoming request
    """
    ctx.request_ctx.set(request)
    ctx.user_ctx.set(request.user)
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
