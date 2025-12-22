"""
Endpoint wrappers
"""

import functools
import inspect
import logging
from collections.abc import Callable, Coroutine
from json.decoder import JSONDecodeError
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pulsarity import ctx
from pulsarity.database.permission import SystemDefaultPerms, UserPermission
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver.auth import requires

_T = TypeVar("_T")

logger = logging.getLogger(__name__)


class JSONBytesResponse(JSONResponse):
    """
    Class used for setting JSON Response data as bytes
    """

    content: bytes

    def render(self, content: bytes) -> bytes:
        return content


def endpoint(
    *permissions: UserPermission,
    requires_auth: bool = True,
    request_model: type[BaseModel] | None = None,
    query_model: type[BaseModel] | None = None,
    response_adapter: TypeAdapter | None = None,
    response_model: type[BaseModel] | None = None,
):
    """
    Decorator for validating request data, user permissions, and
    response data for a route

    :param permission: The permissions required to access the route
    :param request_model: The model to use to validate the request, defaults to None
    :param response_adapter: The adapter model to use to validate the response, defaults to None
    :param response_model: The model to use to validate teh respones, defaults to None
    """
    # pylint: disable=R0912

    def inner(
        func: Callable[..., _T],
    ) -> Callable[[Request], Coroutine[None, None, Response]]:
        num_args = len(inspect.signature(func).parameters.keys())
        try:
            if request_model is not None or query_model is not None:
                assert num_args == 1
            else:
                assert num_args == 0
        except AssertionError as ex:
            raise KeyError(
                f"{func.__name__} does not contain valid number of args"
            ) from ex

        for perm in permissions:
            try:
                assert isinstance(perm, UserPermission)
            except AssertionError as ex:
                raise KeyError(
                    f"{perm} is not a valid {UserPermission.__name__}"
                ) from ex

        if request_model is not None:
            try:
                assert issubclass(request_model, BaseModel)
            except AssertionError as ex:
                raise ValueError(
                    f"{func.__name__} request model is not a subclass of {BaseModel.__name__}"
                ) from ex

        if query_model is not None:
            try:
                assert issubclass(query_model, BaseModel)
            except AssertionError as ex:
                raise ValueError(
                    f"{func.__name__} query model is not a subclass of {BaseModel.__name__}"
                ) from ex

        assert request_model is None or query_model is None, (
            "Request model and query model can not be used together"
        )

        if response_adapter is not None:
            try:
                assert isinstance(response_adapter, TypeAdapter)
            except AssertionError as ex:
                raise ValueError(
                    f"{func.__name__}response adapter is not a instance of {TypeAdapter.__name__}"
                ) from ex

        if response_model is not None:
            try:
                assert issubclass(response_model, BaseModel)
            except AssertionError as ex:
                raise ValueError(
                    f"{func.__name__}response model is not a subclass of {BaseModel.__name__}"
                ) from ex

        assert response_model is None or response_adapter is None, (
            "Response model and response adapter can not be used together"
        )

        if requires_auth:

            @functools.wraps(func)
            @requires(SystemDefaultPerms.AUTHENTICATED, status_code=401)
            @requires(permissions, status_code=403)
            async def wrapper(request: Request) -> Response:
                return await _process_request(
                    func,
                    request,
                    request_model,
                    query_model,
                    response_adapter,
                    response_model,
                )

        else:

            @functools.wraps(func)
            async def wrapper(request: Request) -> Response:
                return await _process_request(
                    func,
                    request,
                    request_model,
                    query_model,
                    response_adapter,
                    response_model,
                )

        return wrapper

    return inner


async def _process_request(
    func: Callable,
    request: Request,
    request_model: type[BaseModel] | None,
    query_model: type[BaseModel] | None,
    response_adapter: TypeAdapter | None,
    response_model: type[BaseModel] | None,
) -> Response:
    """
    Processes the incoming request
    """
    # pylint: disable=R0913,R0917

    ctx.request_ctx.set(request)
    ctx.user_ctx.set(request.user)

    if request_model is not None:
        try:
            data = await request.body()
            parsed_model = request_model.model_validate_json(data)
        except (JSONDecodeError, ValidationError):
            return Response(status_code=400)

        endpoint_result = await ensure_async(func, parsed_model)

    elif query_model is not None:
        try:
            parsed_model = query_model.model_validate(request.query_params)
        except (JSONDecodeError, ValidationError):
            return Response(status_code=400)

        endpoint_result = await ensure_async(func, parsed_model)

    else:
        endpoint_result = await ensure_async(func)

    if response_adapter is not None:
        return _process_response_adapter(func, response_adapter, endpoint_result)

    if isinstance(endpoint_result, Response):
        return endpoint_result

    if response_model is not None:
        return _process_response_model(func, response_model, endpoint_result)

    return Response()


def _process_response_adapter(
    func: Callable, response_adapter: TypeAdapter, endpoint_result: _T
) -> Response:
    """
    Serialize the endpoint result to a response
    """
    if endpoint_result is None:
        return Response(status_code=204)

    try:
        model = response_adapter.validate_python(endpoint_result, from_attributes=True)
    except ValidationError:
        logger.exception(
            "Returned object from {%s} does not match response adapter {%s}",
            func.__name__,
            response_adapter,
        )
        return Response(status_code=500)

    return JSONBytesResponse(response_adapter.dump_json(model))


def _process_response_model(
    func: Callable, response_model: type[BaseModel], endpoint_result: _T
) -> Response:
    """
    Serialize the endpoint result to a response
    """
    if endpoint_result is None:
        return Response(status_code=204)

    try:
        model = response_model.model_validate(endpoint_result, from_attributes=True)
    except ValidationError:
        logger.exception(
            "Returned object from %s does not match response model %s",
            func.__name__,
            response_model.__name__,
        )
        return Response(status_code=500)

    return JSONResponse(model.model_dump_json())
