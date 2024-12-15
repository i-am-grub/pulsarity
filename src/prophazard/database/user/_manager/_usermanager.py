from typing_extensions import override

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..._base._basemanager import _BaseManager
from .._orm.user import User, Role


class UserManager(_BaseManager[User]):

    @property
    @override
    def _table_class(self) -> type[User]:
        """
        Property holding the respective class type for the database object

        :return Type[User]: Returns the User class
        """
        return User

    @_BaseManager._optional_session
    async def get_by_uuid(self, session: AsyncSession, uuid: str) -> User | None:
        """
        Attempt to retrieve a user by uuid

        :param AsyncSession session: _description_
        :param str uuid: _description_
        :return User | None: _description_
        """
        statement = select(self._table_class).where(self._table_class.auth_id == uuid)
        return await session.scalar(statement)

    @_BaseManager._optional_session
    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        """
        Attempt to retrieve a user by username

        :param AsyncSession session: _description_
        :param str username: _description_
        :return User | None: _description_
        """
        statement = select(self._table_class).where(
            self._table_class.username == username
        )
        return await session.scalar(statement)

    @_BaseManager._optional_session
    async def verify_persistant_user(
        self, session: AsyncSession, username: str, roles: set[Role]
    ) -> None:
        """
        Verify permissions are setup for a role.

        :param AsyncSession session: _description_
        :param str name: Name of role to check
        :param set[Permission] permissions: Set of permissions to apply
        """
        if await self.get_by_username(session, username) is None:
            user = User("admin", roles, persistent=True)
            await user.set_password("password")
            await self.add(session, user)
            await session.flush()
