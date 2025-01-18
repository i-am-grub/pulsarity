"""
User objects management
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ..._base import _UserBase
from ._usermanager import _UserManager
from ._rolemanager import _RoleManager
from ._permissionmanager import _PermissionManager


class UserDatabaseManager:
    """
    Database manager for user related objects
    """

    def __init__(self, *, filename: str = ":memory:"):
        """
        Class initialization

        :param filename: Filename for the database, defaults to ":memory:"
        """

        self.engine = create_async_engine(f"sqlite+aiosqlite:///{filename}", echo=False)
        default_session_maker = self.new_session_maker()

        self.users = _UserManager(default_session_maker)
        self.roles = _RoleManager(default_session_maker)
        self.permissions = _PermissionManager(default_session_maker)

    async def setup(self) -> None:
        """
        Setup the database connection. Used at server startup.
        """

        async with self.engine.begin() as conn:
            await conn.run_sync(_UserBase.metadata.create_all)

    async def verify_persistant_objects(
        self, defualt_username: str, default_password: str
    ):
        """
        Verify that the default object are in the database.

        :param defualt_username: Default username to use for the admin user
        :param default_password: Default password to use for the admin user
        """
        await self.permissions.verify_persistant()
        permissions = await self.permissions.get_all(None)
        await self.roles.verify_persistant_role(None, "SYSTEM_ADMIN", set(permissions))

        roles = set()
        if (role := await self.roles.role_by_name(None, "SYSTEM_ADMIN")) is not None:
            roles.add(role)

        await self.users.verify_persistant_user(
            None, defualt_username, default_password, roles
        )

    async def shutdown(self) -> None:
        """
        Shutdown the database connection.
        """

        await self.engine.dispose()

    def new_session_maker(self, *args, **kwargs) -> async_sessionmaker[AsyncSession]:
        """A wrapper for async_sessionmaker with `autoflush`, `autocommit`, and
        `expire_on_commit` set to `False`

        :param expire_on_commit: _description_, defaults to False
        :return: _description_
        :rtype: async_sessionmaker
        """
        kwargs["autoflush"] = False
        kwargs["autocommit"] = False
        kwargs["expire_on_commit"] = False

        return async_sessionmaker(self.engine, *args, **kwargs)
