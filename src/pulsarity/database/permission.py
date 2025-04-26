"""
ORM classes for Permission data
"""

from __future__ import annotations

from enum import StrEnum, auto
from typing import TYPE_CHECKING

from tortoise import fields

from .base import _PulsarityBase

if TYPE_CHECKING:
    from .role import Role


class Permission(_PulsarityBase):
    """
    Role for the application
    """

    # pylint: disable=R0903

    value = fields.CharField(max_length=64, unique=True)
    """Name of role"""
    persistent = fields.BooleanField(default=False)
    """Entry is persistent in database"""
    _roles: fields.ManyToManyRelation[Role]
    """Roles permission is assigned to"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "system"
        table = "permission"

    def __init__(self, value: UserPermission, *, persistent=False):
        """
        Class initialization

        :param value: The string to map the value to
        :param persistent: When set to `True` prevents the object
        from being deleted from the database, defaults to False
        """
        super().__init__()

        self.value = value
        self.persistent = persistent

    @classmethod
    async def verify_persistant(cls) -> None:
        """
        Verify all nessessary permissions are in the user database.
        """

        permissions: set[str] = set(await cls.all().values_list("value", flat=True))  # type: ignore

        permissions_add = []

        for permission_class in UserPermission.__subclasses__():

            persistent = permission_class is SystemDefaultPerms

            for enum in permission_class:

                if enum not in permissions:
                    permissions_add.append(Permission(enum, persistent=persistent))

        await cls.bulk_create(permissions_add)


class UserPermission(StrEnum):
    """
    Parent class for all user permissions enums

    Plugins can inherit from this class to add
    and use custom permissions.
    """


class SystemDefaultPerms(UserPermission):
    """
    Default user permissions for the system
    """

    AUTHENTICATED = auto()

    EVENT_WEBSOCKET = auto()
    SYSTEM_CONTROL = auto()

    READ_PILOTS = auto()
    WRITE_PILOTS = auto()
    RACE_EVENTS = auto()
