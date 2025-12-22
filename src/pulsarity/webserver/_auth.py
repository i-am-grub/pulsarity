"""
Authorization and permission enforcement
"""

import functools
import inspect
from collections.abc import Callable, Iterable, Sequence
from typing import Any, ParamSpec
from urllib.parse import urlencode
from uuid import UUID

from starlette._utils import is_async_callable
from starlette.authentication import (
    AuthenticationBackend,
    BaseUser,
    UnauthenticatedUser,
)
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocket

from pulsarity.database.permission import UserPermission
from pulsarity.database.user import User

_P = ParamSpec("_P")


class PulsarityCredentials:
    """
    Reimplementation of starlette's `AuthCredentials`
    """

    # pylint: disable=R0903

    def __init__(self, scopes: Sequence[str] | None = None):
        self.scopes = set() if scopes is None else set(scopes)


def has_required_scope(conn: HTTPConnection, scopes: Iterable[str]) -> bool:
    """
    Reimplementation of starlette's `has_required_scope`
    """
    return set(scopes).issubset(conn.auth.scopes)


def requires(
    scopes: str | Sequence[str],
    status_code: int = 403,
    redirect: str | None = None,
) -> Callable[[Callable[_P, Any]], Callable[_P, Any]]:
    """
    Reimplementation of starlette's `requires` decorator
    """
    # pylint: disable=W0719
    scopes_set = {scopes} if isinstance(scopes, str) else set(scopes)

    def decorator(
        func: Callable[_P, Any],
    ) -> Callable[_P, Any]:
        sig = inspect.signature(func)
        for idx, parameter in enumerate(sig.parameters.values()):
            if parameter.name in ("request", "websocket"):
                type_ = parameter.name
                break
        else:
            raise Exception(
                f'No "request" or "websocket" argument on function "{func}"'
            )

        if type_ == "websocket":

            @functools.wraps(func)
            async def websocket_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
                websocket = kwargs.get(
                    "websocket", args[idx] if idx < len(args) else None
                )
                assert isinstance(websocket, WebSocket)

                if not has_required_scope(websocket, scopes_set):
                    await websocket.close()
                else:
                    await func(*args, **kwargs)

            return websocket_wrapper

        if is_async_callable(func):

            @functools.wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Any:
                request = kwargs.get("request", args[idx] if idx < len(args) else None)
                assert isinstance(request, Request)

                if not has_required_scope(request, scopes_set):
                    if redirect is not None:
                        orig_request_qparam = urlencode({"next": str(request.url)})
                        next_url = f"{request.url_for(redirect)}?{orig_request_qparam}"
                        return RedirectResponse(url=next_url, status_code=303)
                    raise HTTPException(status_code=status_code)
                return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Any:
            request = kwargs.get("request", args[idx] if idx < len(args) else None)
            assert isinstance(request, Request)

            if not has_required_scope(request, scopes_set):
                if redirect is not None:
                    orig_request_qparam = urlencode({"next": str(request.url)})
                    next_url = f"{request.url_for(redirect)}?{orig_request_qparam}"
                    return RedirectResponse(url=next_url, status_code=303)
                raise HTTPException(status_code=status_code)
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator


class PulsarityUser(BaseUser):
    """
    User of the authentication system
    """

    def __init__(self, db_user: User):
        self._auth_id = db_user.auth_id.hex
        self._username = db_user.username
        self._display_name = db_user.display_name

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def identity(self) -> str:
        return self._auth_id

    async def get_permissions(self) -> set[str]:
        """
        Get the permissions for the user

        :return: The set of permissions
        """

        if self._auth_id is None:
            return set()

        uuid = UUID(hex=self._auth_id)
        user = await User.get_by_uuid_prefetch(uuid)

        if user is None:
            return set()

        return user.permissions

    async def has_permission(self, permission: UserPermission) -> bool:
        """
        Check a user for valid permissions

        :param permission: The user permission to check for
        :return: Status of the user have the permission. Returning
        True verifies that the permission has been granted.
        """

        permissions = await self.get_permissions()
        return permission in permissions


class PulsarityAuthBackend(AuthenticationBackend):
    """
    Authentication middleware
    """

    # pylint: disable=R0903

    async def authenticate(self, conn):
        """
        Checks session info to verify if the user is authenticated or not
        """
        if (uuid_hex := conn.session.get("auth_id")) is not None:
            user_uuid = UUID(hex=uuid_hex)
            user = await User.get_by_uuid_prefetch(user_uuid)

            if user is not None:
                return PulsarityCredentials(user.permissions), PulsarityUser(user)

        return PulsarityCredentials(), UnauthenticatedUser()
