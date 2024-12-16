from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..._base import _UserBase
from .permission import Permission
from ....auth._permissions import UserPermission

role_permission_association = Table(
    "role_permission_mapping",
    _UserBase.metadata,
    Column("role", ForeignKey("role.id"), primary_key=True),
    Column("permission", ForeignKey("permission.id"), primary_key=True),
)


class Role(_UserBase):
    """
    Role for the application
    """

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(unique=True)
    """Name of role"""
    _permissions: Mapped[set[Permission]] = relationship(
        secondary=role_permission_association
    )
    """Permissions granted to a role"""

    def __init__(
        self,
        name: str,
        *,
        permissions: set[Permission] = set(),
        persistent: bool = False
    ):
        self.name = name
        self._permissions = permissions
        self._persistent = persistent

    async def get_permissions(self) -> set[UserPermission]:
        permissions = set()
        permissions_: set[Permission] = await self.awaitable_attrs._permissions

        for permission in permissions_:
            permissions.add(permission.value)

        return permissions

    def set_permissions(self, value: set[Permission]) -> None:
        self._permissions = value
