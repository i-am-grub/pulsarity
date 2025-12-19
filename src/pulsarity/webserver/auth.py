"""
Authorization and permission enforcement
"""

from uuid import UUID

from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    UnauthenticatedUser,
)

from pulsarity.database.permission import UserPermission
from pulsarity.database.user import User


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
        user = await User.get_by_uuid(uuid)

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
            user = await User.get_by_uuid(user_uuid)

            if user is not None:
                return AuthCredentials(user.permissions), PulsarityUser(user)

        return AuthCredentials(), UnauthenticatedUser()
