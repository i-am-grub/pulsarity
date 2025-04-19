"""
Endpoint wrappers
"""

import asyncio
import functools
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from ..database.permission import UserPermission
from .auth import PulsarityUser

T = TypeVar("T")
P = ParamSpec("P")


async def _run_endpoint(func: Callable[..., Any | None], *args, **kwargs) -> Any | None:

    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    return await asyncio.to_thread(func, *args, **kwargs)


def endpoint(
    *,
    request_model: BaseModel | None = None,
    permission: UserPermission | None = None,
    response_model: BaseModel | None = None,
):
    """
    Decorator for validating request data, user permissions, and
    response data for a route

    :param request_model: _description_, defaults to None
    :param permission: _description_, defaults to None
    :param response_model: _description_, defaults to None
    """

    def inner(
        func: Callable[P, T],
    ) -> Callable[[Request], Coroutine[None, None, Response]]:

        @functools.wraps(func)
        async def wrapper(request: Request) -> Response:
            if request_model is not None:
                data = await request.json()
                try:
                    request_model.model_validate_json(data)
                except ValidationError:
                    return HTMLResponse()

            user: PulsarityUser = request.user

            endpoint_result = await _run_endpoint(func)

            if response_model is not None and endpoint_result is not None:
                try:
                    response_model.model_validate(endpoint_result)
                except ValidationError:
                    return HTMLResponse()
                return JSONResponse(endpoint_result)

            return HTMLResponse()

        return wrapper

    return inner
