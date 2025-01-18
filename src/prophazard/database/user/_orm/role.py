"""
ORM classes for Role data
"""

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..._base import _UserBase
from .permission import Permission

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

    # pylint: disable=W0212

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
        permissions: set[Permission] | None = None,
        persistent: bool = False,
    ):
        """
        Class initalization

        :param name: Name of the role. It should be unique from all other
        roles in the system. Saves an uppercase version of the string provided.
        :param permissions: The permissions for the
        role, defaults to None
        :param persistent: When set to `True` prevents the object
        from being deleted from the database, defaults to False
        """
        self.name = name.upper()
        self._permissions = set() if permissions is None else permissions
        self.persistent = persistent

    async def get_permissions(self) -> set[str]:
        """
        Gets the permissions for the role. Should be ran while the database
        session is still active.

        :return: The set of permissions
        """
        permissions = set()
        permissions_: set[Permission] = await self.awaitable_attrs._permissions

        for permission in permissions_:
            permissions.add(permission.value)

        return permissions

    def set_permissions(self, value: set[Permission]) -> None:
        """
        Set the permissions for a role. Overwrites any previous values

        :param value: The permissions to set
        """

        self._permissions = value
