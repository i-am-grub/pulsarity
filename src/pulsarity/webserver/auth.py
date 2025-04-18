"""
Authorization and permission enforcement
"""

import asyncio
import base64
import binascii
from uuid import UUID

from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
)

from ..database.permission import UserPermission
from ..database.user import User


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
        user = await User.get_or_none(auth_id=uuid)

        if user is None:
            return set()

        return await user.permissions

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

    async def authenticate(self, conn):
        """
        Temporarily utilize basic auth example
        """

        if "Authorization" not in conn.headers:
            return

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError("Invalid basic auth credentials") from exc

        username, _, password = decoded.partition(":")

        return await self.verify_credentials(username, password)

    async def verify_credentials(
        self, username, password
    ) -> tuple[AuthCredentials, BaseUser] | None:
        """
        Checks the username and password against a set of database values

        :param username: The username to search for
        :param password: The password of the user to verify
        :return: The credentials and authenticated user
        """

        user = await User.get_or_none(username=username)

        if user is not None and await user.verify_password(password):
            permissions = list(await user.permissions)

            asyncio.create_task(user.update_user_login_time())
            asyncio.create_task(user.check_for_rehash(password))

            return AuthCredentials(permissions), PulsarityUser(user)

        return None
