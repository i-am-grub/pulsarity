"""
ORM classes for Role data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from .base import _PHDataBase
from .permission import Permission

if TYPE_CHECKING:
    from .user import User


class Role(_PHDataBase):
    """
    Role for the application
    """

    # pylint: disable=W0212,R0903

    name = fields.CharField(max_length=64, unique=True)
    """Name of role"""
    _users: fields.ManyToManyRelation[User]
    """Users role is assigned to"""
    _permissions: fields.ManyToManyRelation[Permission] = fields.ManyToManyField(
        "system.Permission", related_name="_roles", through="role_permission"
    )
    """Permissions granted to a role"""
    persistent = fields.BooleanField(default=False)
    """Entry is persistent in database"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "system"
        table = "role"

    async def get_permissions(self) -> set[str]:
        """
        Gets the permissions for the role. Should be ran while the database
        session is still active.

        :return: The set of permissions
        """
        values = set(await self._permissions.all().values_list("value", flat=True))
        return values  # type: ignore

    async def set_permissions(self, *permissions: Permission) -> None:
        """
        Set the permissions for a role. Overwrites any previous values

        :param value: The permissions to set
        """
        await self._permissions.clear()
        await self._permissions.add(*permissions)
