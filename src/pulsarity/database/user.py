"""
ORM classes for User data
"""

import asyncio
import logging
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from tortoise import fields

from pulsarity.database._base import PulsarityBase
from pulsarity.database.role import Role
from pulsarity.utils.config import configs

logger = logging.Logger(__name__)

_PH = PasswordHasher()


async def _generate_hash(password: str) -> str:
    """
    Generates a hash of the provided password without blocking.

    :param password: The password to hash.
    :return: The hashed password
    """
    loop = asyncio.get_running_loop()

    try:
        result = await loop.run_in_executor(None, _PH.hash, password)
    except HashingError:
        logger.exception("Failed to hash password")
        raise

    return result


class User(PulsarityBase):
    """
    User for the application
    """

    # pylint: disable=W0212,R0903

    auth_id = fields.UUIDField(default=uuid4)
    """The UUID associated with the user"""
    username = fields.CharField(max_length=32, unique=True)
    """Username of user"""
    first_name = fields.CharField(max_length=32, null=True)
    """First name of user"""
    last_name = fields.CharField(max_length=32, null=True)
    """Last name of user"""
    _password_hash = fields.TextField(null=True)
    """Hash of the user's password"""
    _roles: fields.ManyToManyRelation[Role] = fields.ManyToManyField(
        "system.Role", related_name="_users", through="user_role"
    )
    """The role of the user"""
    last_login = fields.DatetimeField(null=True)
    """Time of last authenication"""
    reset_required = fields.BooleanField(default=True)
    """A flag signaling the user's password should be reset"""
    persistent = fields.BooleanField(default=False)
    """Entry is persistent in database"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "system"
        table = "user"

    @property
    def display_name(self) -> str:
        """
        The display name for the user when authenticated

        :return: The name to display
        """
        if self.first_name is not None and self.last_name is not None:
            return f"{self.first_name} {self.last_name}"

        if self.first_name is not None:
            return f"{self.first_name}"

        return self.username

    @property
    async def permissions(self) -> set[str]:
        """
        Gets the permissions for the user. Can only be used when a
        session to the database has not been closed

        :return: The set of permissions
        """
        permissions: set[str] = set()

        async for role in self._roles:
            permissions_: set[str] = await role.get_permissions()
            permissions.update(permissions_)

        return permissions

    async def verify_password(self, password: str) -> bool:
        """
        Checks a hash of the provided password against the hash in the database.

        :param password: The password to hash.
        :return: Whether the comparsion of the hash was sucessful or not.
        """

        if self._password_hash is None:
            return False

        loop = asyncio.get_running_loop()

        try:
            result = await loop.run_in_executor(
                None, _PH.verify, self._password_hash, password
            )
        except VerifyMismatchError:
            logger.warning(
                "Stored hash for %s does not match the provided password", self.username
            )
            return False
        except VerificationError:
            logger.exception("Verification failed for %s", self.username)
            return False
        except InvalidHashError:
            logger.exception("Invalid hash error for %s", self.username)
            return False

        return result

    async def check_password_rehash(self) -> bool:
        """
        Checks if the user's password needs to be rehashed due to a
        configuration change.

        :return: The status of the check
        """
        if self._password_hash is None:
            return True

        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            None, _PH.check_needs_rehash, self._password_hash
        )
        return result

    async def update_user_password(self, password: str) -> None:
        """
        Updates a user's password hash in the database.

        :param password: The password to hash and store
        """
        hashed_password = await _generate_hash(password)
        await self.filter(id=self.id).update(_password_hash=hashed_password)

    @classmethod
    async def get_by_uuid(cls, uuid: UUID) -> Self | None:
        """
        Attempt to retrieve a user by uuid

        :param uuid: The uuid to search for
        """
        return await cls.get_or_none(auth_id=uuid)

    @classmethod
    async def get_by_username(cls, username: str) -> Self | None:
        """
        Attempt to retrieve a user by username

        :param username: The username to search for
        """
        return await cls.get_or_none(username=username)

    @classmethod
    async def verify_persistant(cls) -> None:
        """
        Verify all system roles are in the user database.
        """
        default_username = str(configs.get_config("SECRETS", "DEFAULT_USERNAME"))
        default_password = str(configs.get_config("SECRETS", "DEFAULT_PASSWORD"))

        user, created = await User.get_or_create(
            username=default_username, persistent=True
        )

        role = await Role.get_or_none(name="SYSTEM_ADMIN")
        if role is not None:
            await user._roles.add(role)
        else:
            raise RuntimeError("Role for system admin does not exist")

        if created:
            await user.update_user_password(default_password)

    async def check_for_rehash(self, password: str) -> None:
        """
        Checks to see if a user's hash needs to be updated. Update it
        automatically automatically if it does.

        :param password: The password to rehash if necessary
        """

        if await self.check_password_rehash():
            await self.update_user_password(password)

    async def update_user_login_time(self) -> None:
        """
        Update a user's `last_login` time.
        """
        await self.filter(id=self.id).update(last_login=datetime.now())

    async def update_password_required(self, status: bool) -> None:
        """
        Change the status of the `reset_required` attribute for a user

        :param status: The value to set the status to
        """
        await self.filter(id=self.id).update(reset_required=status)
