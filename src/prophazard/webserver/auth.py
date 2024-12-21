from typing import TypeVar, ParamSpec
from collections.abc import Callable, Awaitable
from functools import wraps

from quart_auth import Unauthorized

from ..extensions import current_app, current_user

from ..database.user._enums import UserPermission

T = TypeVar("T")
P = ParamSpec("P")


class InvalidPermissions(Unauthorized):
    """
    Raised when a user attempts to reach a resource without proper permissions.
    """

    ...


def permission_required(permission: UserPermission):
    """A decorator to restrict route access to authenticated users
    with granted permissions.

    This should be used to wrap a route handler (or view function) to
    enforce that only authenticated requests can access it. Note that
    it is important that this decorator be wrapped by the route
    decorator and not vice, versa, as below.

    .. code-block:: python

        @app.route('/')
        @permission_required('permission')
        async def index():
            ...

    If the request is not authenticated or permissions not granted a
    `quart.exceptions.Unauthorized` exception will be raised.

    """

    def inner(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:

            if not await current_user.is_authenticated:
                raise Unauthorized()
            elif not await current_user.has_permission(permission):
                raise InvalidPermissions()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    return inner
