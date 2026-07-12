"""
ORM classes for User data
"""

import asyncio
import logging
from datetime import UTC, datetime
from functools import cached_property
from typing import Self
from uuid import UUID, uuid4

import async_lru
from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from tortoise import fields

from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.database.role import Role
from pulsarity.utils import config

logger = logging.getLogger(__name__)

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


class User(_PulsarityBase):
    """
    User for the application
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "system"
        table = "user"

    auth_id = fields.UUIDField(default=uuid4, index=True)
    """The UUID associated with the user"""
    username = fields.CharField(max_length=32, unique=True)
    """Username of user"""
    first_name = fields.CharField(max_length=32, null=True)
    """First name of user"""
    last_name = fields.CharField(max_length=32, null=True)
    """Last name of user"""
    _password_hash = fields.TextField(null=True)
    """Hash of the user's password"""
    roles: fields.ManyToManyRelation[Role] = fields.ManyToManyField(
        "system.Role",
        related_name="users",
        through="user_role",
    )
    """The role of the user"""
    last_login = fields.DatetimeField(null=True)
    """Time of last authenication"""
    reset_required = fields.BooleanField(default=True)
    """A flag signaling the user's password should be reset"""
    persistent = fields.BooleanField(default=False)
    """Entry is persistent in database"""

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

    @cached_property
    def permissions(self) -> set[str]:
        """
        Gets the permissions for the user. Can only be used when roles
        and permissions are prefetched for the user

        :return: The set of permissions
        """
        permissions: set[str] = set()

        for role in self.roles:
            permissions.update({perm.value for perm in role.permissions})

        return permissions

    async def verify_password(self, password: str) -> bool:
        """
        Checks a hash of the provided password against the hash in the database
        for a user.
        """
        if not self._password_hash:
            return False

        return await self._verify_password(self._password_hash, password, self.auth_id)

    @classmethod
    async def verify_password_uuid(cls, uuid: UUID, password: str) -> bool:
        """
        Checks a hash of the provided password against the hash in the database by
        UUID.
        """
        pw_hash: str | None = await cls.get_or_none(auth_id=uuid).values_list(  # type: ignore
            "_password_hash",
            flat=True,
        )

        if pw_hash is None:
            return False

        return await cls._verify_password(pw_hash, password, uuid)

    @classmethod
    async def _verify_password(cls, pw_hash: str, password: str, uuid: UUID) -> bool:
        """
        Checks a hash of the provided password against the hash in the database.
        """
        loop = asyncio.get_running_loop()

        try:
            result = await loop.run_in_executor(
                None,
                _PH.verify,
                pw_hash,
                password,
            )
        except VerifyMismatchError:
            logger.warning(
                "Stored hash for %s does not match the provided password",
                uuid.hex,
            )
            return False
        except VerificationError:
            logger.exception("Verification failed for %s", uuid.hex)
            return False
        except InvalidHashError:
            logger.exception("Invalid hash error for %s", uuid.hex)
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

        return await loop.run_in_executor(
            None,
            _PH.check_needs_rehash,
            self._password_hash,
        )

    @classmethod
    async def update_user_password(cls, uuid: UUID, password: str) -> None:
        """
        Updates a user's password hash in the database.

        :param password: The password to hash and store
        """
        hashed_password = await _generate_hash(password)
        await cls.filter(auth_id=uuid).update(_password_hash=hashed_password)

    @classmethod
    async def update_user_password_and_status(cls, uuid: UUID, password: str) -> None:
        """
        Updates a user's password hash in the database.

        :param password: The password to hash and store
        """
        hashed_password = await _generate_hash(password)
        await cls.filter(auth_id=uuid).update(
            _password_hash=hashed_password,
            reset_required=False,
        )

    @classmethod
    async def get_by_uuid(cls, uuid: UUID) -> Self | None:
        """
        Attempt to retrieve a user by uuid.

        :param uuid: The uuid to search for
        """
        return await cls.get_or_none(auth_id=uuid)

    @classmethod
    @async_lru.alru_cache()
    async def get_by_uuid_prefetch(cls, uuid: UUID) -> Self | None:
        """
        Attempt to retrieve a user by uuid. A successful retrieval will
        prefetch data down to the permissions level for the user.

        :param uuid: The uuid to search for
        """
        return await cls.get_or_none(auth_id=uuid).prefetch_related(
            "roles__permissions",
        )

    @classmethod
    async def get_by_username(cls, username: str) -> Self | None:
        """
        Attempt to retrieve a user by username

        :param username: The username to search for
        """
        return await cls.get_or_none(username=username)

    @classmethod
    async def get_by_username_prefetch(cls, username: str) -> Self | None:
        """
        Attempt to retrieve a user by username

        :param username: The username to search for
        """
        return await cls.get_or_none(username=username).prefetch_related(
            "roles__permissions",
        )

    @classmethod
    async def verify_persistant(cls) -> None:
        """
        Verify all system roles are in the user database.
        """
        default_username = config.config_manager.secrets.default_username
        default_password = config.config_manager.secrets.default_password

        user, created = await cls.get_or_create(
            username=default_username,
            persistent=True,
        )

        role = await Role.get_or_none(name="SYSTEM_ADMIN")
        if role is not None:
            await user.roles.add(role)
        else:
            msg = "Role for system admin does not exist"
            raise RuntimeError(msg)

        if created:
            await cls.update_user_password(user.auth_id, default_password)

    async def check_for_rehash(self, password: str) -> None:
        """
        Checks to see if a user's hash needs to be updated. Update it
        automatically automatically if it does.

        :param password: The password to rehash if necessary
        """

        if await self.check_password_rehash():
            await self.update_user_password(self.auth_id, password)

    async def update_user_login_time(self) -> None:
        """
        Update a user's `last_login` time.
        """
        await self.filter(id=self.id).update(last_login=datetime.now(tz=UTC))

    @classmethod
    async def update_password_required(cls, uuid: UUID, status: bool) -> None:
        """
        Change the status of the `reset_required` attribute for a user

        :param status: The value to set the status to
        """
        await cls.filter(auth_id=uuid).update(reset_required=status)
