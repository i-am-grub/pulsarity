"""
Authorization and permission enforcement
"""

import functools
import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ParamSpec
from urllib.parse import urlencode
from uuid import UUID

from starlette.authentication import (
    AuthenticationBackend,
    BaseUser,
)
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocket

from pulsarity.database import Role
from pulsarity.database.user import User

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


_P = ParamSpec("_P")


class PulsarityCredentials:
    """
    Reimplementation of starlette's `AuthCredentials`
    """

    __slots__ = ("scopes",)

    def __init__(self, scopes: Iterable[str] | None = None):
        self.scopes = set() if scopes is None else set(scopes)


def has_required_scope(conn: HTTPConnection, scopes: Iterable[str]) -> bool:
    """
    Reimplementation of starlette's `has_required_scope`. Assumes that the
    connection scope container is set based.
    """
    connection_scopes: set = conn.auth.scopes
    return connection_scopes.issuperset(scopes)


def requires(
    scopes: str | Sequence[str],
    status_code: int = 403,
    redirect: str | None = None,
) -> Callable[[Callable[_P, Any]], Callable[_P, Any]]:
    """
    Reimplementation of starlette's `requires` decorator
    """
    # pylint: disable=W0719
    scopes_list = (scopes,) if isinstance(scopes, str) else tuple(scopes)

    def decorator(
        func: Callable[_P, Any],
    ) -> Callable[_P, Any]:
        sig = inspect.signature(func)
        idx = -1
        for parameter in sig.parameters.values():
            idx += 1
            if parameter.name in ("request", "websocket"):
                type_ = parameter.name
                break
        else:
            msg = f'No "request" or "websocket" argument on function "{func}"'
            raise RuntimeError(msg)

        if type_ == "websocket":

            @functools.wraps(func)
            async def websocket_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
                websocket = kwargs.get(
                    "websocket", args[idx] if idx < len(args) else None
                )
                if isinstance(websocket, WebSocket):
                    if not has_required_scope(websocket, scopes_list):
                        await websocket.close()
                    else:
                        await func(*args, **kwargs)
                else:
                    msg = "Websocket object not provided as valid arg"
                    raise TypeError(msg)

            return websocket_wrapper

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Any:
                request = kwargs.get("request", args[idx] if idx < len(args) else None)
                if isinstance(request, Request):
                    if not has_required_scope(request, scopes_list):
                        if redirect is not None:
                            orig_request_qparam = urlencode({"next": str(request.url)})
                            next_url = (
                                f"{request.url_for(redirect)}?{orig_request_qparam}"
                            )
                            return RedirectResponse(url=next_url, status_code=303)
                        raise HTTPException(status_code=status_code)
                    return await func(*args, **kwargs)
                msg = "Request object not provided as valid arg"
                raise TypeError(msg)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Any:
            request = kwargs.get("request", args[idx] if idx < len(args) else None)
            if isinstance(request, Request):
                if not has_required_scope(request, scopes_list):
                    if redirect is not None:
                        orig_request_qparam = urlencode({"next": str(request.url)})
                        next_url = f"{request.url_for(redirect)}?{orig_request_qparam}"
                        return RedirectResponse(url=next_url, status_code=303)
                    raise HTTPException(status_code=status_code)
                return func(*args, **kwargs)

            msg = "Request object not provided as valid arg"
            raise TypeError(msg)

        return sync_wrapper

    return decorator


class PulsarityUser(BaseUser, ABC):
    """
    Abstract base class for user authentication
    """

    @property
    @abstractmethod
    def username(self) -> str:
        """
        Username of the authenticated user
        """


class PulsarityAuthenticatedUser(PulsarityUser):
    """
    Container for an authenticated user
    """

    __slots__ = ("_auth_id", "_display_name", "_username")

    def __init__(self, db_user: User) -> None:
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

    @property
    def username(self) -> str:
        """
        _summary_

        :return: _description_
        """
        return self._username


class PulsarityUnauthenticatedUser(PulsarityUser):
    """
    An unauthenticated user
    """

    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return ""

    @property
    def identity(self) -> str:
        return ""

    @property
    def username(self) -> str:
        return ""


class PulsarityAuthBackend(AuthenticationBackend):
    """
    Authentication middleware
    """

    __slots__ = ()

    async def authenticate(self, conn):
        """
        Checks session info to verify if the user is authenticated or not
        """
        if (uuid_hex := conn.session.get("auth_id")) is not None:
            user_uuid = UUID(hex=uuid_hex)
            user = await User.get_by_uuid_prefetch(user_uuid)

            if user is not None:
                return PulsarityCredentials(
                    user.permissions
                ), PulsarityAuthenticatedUser(user)

        role = await Role.get(name="UNAUTHENTICATED").prefetch_related("permissions")
        unauth_perms = await role.get_permissions()
        return PulsarityCredentials(unauth_perms), PulsarityUnauthenticatedUser()
