"""
Endpoint wrappers
"""

import functools
import inspect
from collections.abc import Callable, Coroutine
from json.decoder import JSONDecodeError
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pulsarity import ctx
from pulsarity.database.permission import UserPermission
from pulsarity.utils.asyncio import ensure_async
from pulsarity.webserver.validation import BaseResponse

_T = TypeVar("_T")

_bad_response = JSONResponse(BaseResponse(status=False).model_dump_json())
_good_response = JSONResponse(BaseResponse(status=True).model_dump_json())


def endpoint(
    *permissions: UserPermission,
    request_model: type[BaseModel] | None = None,
    response_model: type[BaseModel] | None = None,
):
    """
    Decorator for validating request data, user permissions, and
    response data for a route

    :param permission: The permissions required to access the route
    :param request_model: The model to use to validate the request, defaults to None
    :param response_model: The model to use to validate teh respones, defaults to None
    """

    def inner(
        func: Callable[[BaseModel], _T],
    ) -> Callable[[Request], Coroutine[None, None, Response]]:
        num_args = len(inspect.signature(func).parameters.keys())
        try:
            if request_model is not None:
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

        if response_model is not None:
            try:
                assert issubclass(response_model, BaseModel)
            except AssertionError as ex:
                raise ValueError(
                    f"{func.__name__}response model is not a subclass of {BaseModel.__name__}"
                ) from ex

        @functools.wraps(func)
        @requires(permissions)
        async def wrapper(request: Request) -> Response:
            ctx.request_ctx.set(request)
            ctx.user_ctx.set(request.user)

            if request_model is not None:
                try:
                    data = await request.json()
                    parsed_model = request_model.model_validate(data)
                except (JSONDecodeError, ValidationError):
                    return _bad_response

                endpoint_result = await ensure_async(func, parsed_model)
            else:
                endpoint_result = await ensure_async(func)

            if response_model is not None:
                try:
                    model = response_model.model_validate(endpoint_result)
                except ValidationError:
                    return _bad_response
                return JSONResponse(model.model_dump_json())

            return _good_response

        return wrapper

    return inner
