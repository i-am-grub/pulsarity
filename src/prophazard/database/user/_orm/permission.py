"""
ORM classes for Permission data
"""

from sqlalchemy.orm import Mapped, mapped_column

from ..._base import _UserBase
from .._enums import UserPermission


class Permission(_UserBase):
    """
    Role for the application
    """

    # pylint: disable=R0903

    __tablename__ = "permission"

    value: Mapped[str] = mapped_column(unique=True)
    """Name of role"""

    def __init__(self, value: UserPermission, *, persistent=False):
        """
        Class initialization

        :param UserPermission value: The string to map the value to
        :param bool persistent: When set to `True` prevents the object
        from being deleted from the database, defaults to False
        """
        self.value = value
        self.persistent = persistent
