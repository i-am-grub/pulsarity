"""
ORM classes for Pilot data
"""

import logging
import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    HashingError,
    VerificationError,
    InvalidHashError,
)

from ..._base import _UserBase
from .role import Role
from ....auth._permissions import UserPermission


logger = logging.Logger(__name__)

_ph = PasswordHasher()

user_role_association = Table(
    "user_role_mapping",
    _UserBase.metadata,
    Column("user", ForeignKey("user.id"), primary_key=True),
    Column("role", ForeignKey("role.id"), primary_key=True),
)


class User(_UserBase):
    """
    User for the application
    """

    __tablename__ = "user"

    auth_id: Mapped[UUID] = mapped_column(default=uuid4)
    """The UUID associated with the user"""
    username: Mapped[str] = mapped_column(unique=True)
    """Username of user"""
    first_name: Mapped[str | None] = mapped_column()
    """First name of user"""
    last_name: Mapped[str | None] = mapped_column()
    """Last name of user"""
    _password_hash: Mapped[str | None] = mapped_column()
    """Hash of the user's password"""
    _roles: Mapped[set[Role]] = relationship(secondary=user_role_association)
    """The role of the user"""
    last_login: Mapped[datetime | None] = mapped_column()
    """Time of last authenication"""

    def __init__(
        self,
        username: str,
        roles: set[Role],
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        persistent: bool = False,
    ):
        self.username = username
        self._roles = roles

        self.first_name = first_name if first_name is not None else None
        self.last_name = last_name if last_name is not None else None
        self._persistent = persistent

    @property
    async def permissions(self) -> set[UserPermission]:
        permissions: set[UserPermission] = set()

        roles: set[Role] = await self.awaitable_attrs._roles
        for role in roles:
            permissions = permissions | await role.get_permissions()

        return permissions

    @staticmethod
    async def generate_hash(password: str) -> str:
        """
        Generates a hash of the provided password.

        :param str password: The password to hash.
        :return str: The hashed password
        """
        try:
            result = await asyncio.to_thread(_ph.hash, password)
        except HashingError:
            logger.error("Failed to hash password")
            raise

        return result

    async def verify_password(self, password: str) -> bool:
        """
        Checks a hash of the provided password against the hash in the database.

        :param str password: The password to hash.
        :return bool: Whether the comparsion of the hash was sucessful or not.
        """

        if self._password_hash is None:
            return False

        try:
            result = await asyncio.to_thread(_ph.verify, self._password_hash, password)
        except VerifyMismatchError:
            logger.warning(f"Failed login attempt for {self.username}")
            return False
        except VerificationError:
            logger.error(f"Failed verification error for {self.username}")
            return False
        except InvalidHashError:
            logger.warning(f"Invalid hash error for {self.username}")
            return False
        else:
            return result

    async def check_password_rehash(self) -> bool:
        """
        Checks if the user's password needs to be rehashed due to a
        configuration change.
        """
        if self._password_hash is None:
            return True

        result = await asyncio.to_thread(_ph.check_needs_rehash, self._password_hash)
        return result
