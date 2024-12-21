"""
Stored Enums for the webserver
"""

from enum import StrEnum, auto


class UserPermission(StrEnum):
    """
    Parent class for all user permissions enums

    Plugins can inherit from this class to add
    and use custom permissions.
    """

    ...


class SystemDefaults(UserPermission):
    """
    Default user permissions for the system
    """

    RESET_PASSWORD = auto()
    READ_PILOTS = auto()
    WRITE_PILOTS = auto()
