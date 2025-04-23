"""
Endpoint wrappers
"""

import functools
from collections.abc import Callable, Coroutine
from json.decoder import JSONDecodeError
from typing import ParamSpec, TypeVar

from pydantic import BaseModel, ValidationError
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..database.permission import UserPermission
from ..utils.asyncio import ensure_async
from .validation import BaseResponse

T = TypeVar("T")
P = ParamSpec("P")


def endpoint(
    *permission: UserPermission,
    request_model: type[BaseModel] | None = None,
    response_model: type[BaseModel] | None = None,
):
    """
    Decorator for validating request data, user permissions, and
    response data for a route

    :param request_model: _description_, defaults to None
    :param response_model: _description_, defaults to None
    """
    bad_response = JSONResponse(BaseResponse(status=False).model_dump_json())
    good_response = JSONResponse(BaseResponse(status=True).model_dump_json())

    def inner(
        func: Callable[[Request, BaseModel], T],
    ) -> Callable[[Request], Coroutine[None, None, Response]]:

        @functools.wraps(func)
        @requires([*permission])
        async def wrapper(request: Request) -> Response:

            if request_model is not None:
                try:
                    data = await request.json()
                    parsed_model = request_model.model_validate(data)
                except (JSONDecodeError, ValidationError):
                    return bad_response

                endpoint_result = await ensure_async(func, request, parsed_model)

            else:
                endpoint_result = await ensure_async(func, request)

            if response_model is not None:
                try:
                    model = response_model.model_validate(endpoint_result)
                except ValidationError:
                    return bad_response
                return JSONResponse(model.model_dump_json())

            return good_response

        return wrapper

    return inner
