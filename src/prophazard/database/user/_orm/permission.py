from sqlalchemy.orm import Mapped, mapped_column

from ..._base import _UserBase
from .._enums import UserPermission


class Permission(_UserBase):
    """
    Role for the application
    """

    __tablename__ = "permission"

    value: Mapped[str] = mapped_column(unique=True)
    """Name of role"""

    def __init__(self, value: UserPermission, *, persistent=False):
        self.value = value
        self._persistent = persistent
