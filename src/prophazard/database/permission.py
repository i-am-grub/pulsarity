"""
ORM classes for Permission data
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import StrEnum, auto

from tortoise import fields

from .base import _PHDataBase

if TYPE_CHECKING:
    from .role import Role


class Permission(_PHDataBase):
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

    EVENT_WEBSOCKET = auto()
    SYSTEM_CONTROL = auto()

    READ_PILOTS = auto()
    WRITE_PILOTS = auto()
    RACE_EVENTS = auto()
