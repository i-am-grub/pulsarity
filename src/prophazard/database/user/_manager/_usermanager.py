"""
`User` management
"""

from uuid import UUID
from datetime import datetime

from typing_extensions import override

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..._base._basemanager import _BaseManager
from .._orm.user import User, Role


class _UserManager(_BaseManager[User]):
    """
    Databse manager for the `User` class
    """

    @property
    @override
    def _table_class(self) -> type[User]:
        """
        Property holding the respective class type for the database object

        :return Type[User]: Returns the User class
        """
        return User

    @_BaseManager.optional_session
    async def get_by_uuid(self, session: AsyncSession, uuid: UUID) -> User | None:
        """
        Attempt to retrieve a user by uuid

        :param AsyncSession session: _description_
        :param str uuid: _description_
        :return User | None: _description_
        """
        statement = select(self._table_class).where(self._table_class.auth_id == uuid)
        return await session.scalar(statement)

    @_BaseManager.optional_session
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

    @_BaseManager.optional_session
    async def update_user_password(
        self, session: AsyncSession, user: User, password: str
    ) -> None:
        """
        Updates a user's password hash in the database.

        :param AsyncSession session: _description_
        :param User user: _description_
        :param str password: The password to hash and store
        """
        hashed_passwrod = await user.generate_hash(password)

        statement = (
            update(User)
            .where(User.id == user.id)
            .values(_password_hash=hashed_passwrod)
        )

        await session.execute(statement)
        await session.flush()

    @_BaseManager.optional_session
    async def verify_persistant_user(
        self, session: AsyncSession, username: str, password: str, roles: set[Role]
    ) -> None:
        """
        Verify permissions are setup for a role.

        :param AsyncSession session: _description_
        :param str username: Username of role to check
        :param str password: Password to set if the user doesn't exist yet.
        :param set[Permission] permissions: Set of permissions to apply
        """
        if await self.get_by_username(session, username) is None:
            user = User(username, roles=roles, persistent=True)
            await self.add(session, user)
            await session.flush()
            await self.update_user_password(session, user, password)

    @_BaseManager.optional_session
    async def check_for_rehash(
        self, session: AsyncSession, user: User, password: str
    ) -> None:
        """
        Checks to see if a user's hash needs to be updated. Updates if it does.

        :param AsyncSession session: _description_
        :param User user: _description_
        :param str password: The password to rehash
        """
        if await user.check_password_rehash():
            await self.update_user_password(session, user, password)

    @_BaseManager.optional_session
    async def update_user_login_time(self, session: AsyncSession, user: User) -> None:
        """
        Update a user's `last_login` time.

        :param AsyncSession session: _description_
        :param User user: _description_
        """
        statement = (
            update(User).where(User.id == user.id).values(last_login=datetime.now())
        )

        await session.execute(statement)
        await session.flush()

    @_BaseManager.optional_session
    async def update_password_required(
        self, session: AsyncSession, user: User, status: bool
    ) -> None:
        """
        Change the status of the `reset_required` attribute for a user

        :param AsyncSession session: _description_
        :param User user: _description_
        :param bool status: _description_
        """
        statement = update(User).where(User.id == user.id).values(reset_required=status)

        await session.execute(statement)
        await session.flush()
