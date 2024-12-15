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

    auth_id: Mapped[str] = mapped_column(server_default=str(uuid4()))
    """The UUID associated with the user"""
    username: Mapped[str] = mapped_column(unique=True)
    """Username of user"""
    first_name: Mapped[str | None] = mapped_column()
    """First name of user"""
    last_name: Mapped[str | None] = mapped_column()
    """Last name of user"""
    password_hash: Mapped[str | None] = mapped_column()
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

    async def set_password(self, password: str) -> None:
        """
        Saves a hash of the provided password for the user.

        :param str password: The password to hash.
        """
        loop = asyncio.get_event_loop()
        try:
            hashed_password = await loop.run_in_executor(None, _ph.hash, password)
            self.password_hash = hashed_password
        except HashingError:
            logger.error(f"Failed to hash password for {self.username}")

    async def verify_password(self, password: str) -> bool:
        """
        Checks a hash of the provided password against the hash in the database.

        :param str password: The password to hash.
        :return bool: Whether the comparsion of the hash was sucessful or not.
        """

        if self.password_hash is None:
            return False

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, _ph.verify, self.password_hash, password
            )
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
