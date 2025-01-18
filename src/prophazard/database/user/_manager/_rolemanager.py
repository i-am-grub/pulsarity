"""
`Role` management
"""

from typing_extensions import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..._base._basemanager import _BaseManager
from .._orm import Role, Permission


class _RoleManager(_BaseManager[Role]):
    """
    Databse manager for the `Role` class
    """

    @property
    @override
    def _table_class(self) -> type[Role]:
        """
        Property holding the respective class type for the database object

        :return: Returns the User class
        """
        return Role

    @_BaseManager.optional_session
    async def role_by_name(self, session: AsyncSession, name: str) -> Role | None:
        """
        Get a role by name.

        :param session: _description_
        :param name: Role name
        :return: The retrieved role object.
        """
        statement = select(Role).where(Role.name == name)
        return await session.scalar(statement)

    @_BaseManager.optional_session
    async def verify_persistant_role(
        self, session: AsyncSession, name: str, permissions: set[Permission]
    ) -> None:
        """
        Verify permissions are setup for a role.

        :param session: _description_
        :param name: Name of role to check
        :param permissions: Set of permissions to apply
        """
        if await self.role_by_name(session, name) is None:
            role = Role(name=name, permissions=permissions, persistent=True)
            await self.add(session, role)
            await session.flush()
