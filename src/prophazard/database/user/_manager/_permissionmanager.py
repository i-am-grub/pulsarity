"""
`Permission` management
"""

from typing_extensions import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..._base._basemanager import _BaseManager
from .._orm import Permission
from .._enums import UserPermission, SystemDefaultPerms


class _PermissionManager(_BaseManager[Permission]):
    """
    Databse manager for the `Permission` class
    """

    @property
    @override
    def _table_class(self) -> type[Permission]:
        """
        Property holding the respective class type for the database object

        :return Type[User]: Returns the User class
        """
        return Permission

    @_BaseManager.optional_session
    async def get_user_permissions(self, session: AsyncSession) -> set[str]:
        """
        Get all permission values from the database

        :param AsyncSession session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :return ScalarResult[UserPermission]: User
        """
        statement = select(self._table_class.value)

        permissions: set[str] = set()

        result = await session.stream_scalars(statement)
        async for scalar in result:
            permissions.add(scalar)

        return permissions

    async def verify_persistant(self) -> None:
        """
        Verify all nessessary permissions are in the user database.
        """
        permissions = await self.get_user_permissions(None)

        permissions_add = []

        for permission_class in UserPermission.__subclasses__():

            persistent = permission_class is SystemDefaultPerms

            for enum in permission_class:

                if enum not in permissions:
                    permissions_add.append(Permission(enum, persistent=persistent))

        await self.add_many(None, 0, *permissions_add)
