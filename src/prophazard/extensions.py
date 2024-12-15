from asyncio import Future, get_event_loop

from quart import Quart, Blueprint
from quart import current_app as _current_app
from quart_auth import AuthUser
from quart_auth import current_user as _current_user

from .database.user import UserDatabaseManager, User
from .database.race import RaceDatabaseManager

from .auth._permissions import UserPermission


class RHApplication(Quart):
    """
    RotorHazard web application based on Quart
    """

    try:
        _loop = get_event_loop()
        _user_database: Future[UserDatabaseManager] = _loop.create_future()
        _race_database: Future[RaceDatabaseManager] = _loop.create_future()
    except RuntimeError:
        pass

    async def get_user_database(self) -> UserDatabaseManager:
        return await self._user_database

    def set_user_database(self, manager: UserDatabaseManager) -> None:
        self._user_database.set_result(manager)

    async def get_race_database(self) -> RaceDatabaseManager:
        return await self._race_database

    def set_race_database(self, manager: RaceDatabaseManager) -> None:
        self._race_database.set_result(manager)


class RHBlueprint(Blueprint):
    """
    RotorHazard Quart based blueprints
    """

    ...


current_app: RHApplication = _current_app  # type: ignore


class RHUser(AuthUser):

    async def has_permission(self, permission: UserPermission) -> bool:
        """
        Check a user for valid permissions

        :param UserPermission permission: The user permission to check for
        :return bool: Status of the user have the permission. Returning
        True verifies that the permission has been granted.
        """

        if self._auth_id is None:
            return False

        db_manager = await current_app.get_user_database()

        user: User | None = await db_manager.users.get_by_uuid(None, self._auth_id)
        if user is None:
            return False

        permissions = await user.permissions
        if permission in permissions:
            return True
        else:
            return False


current_user: RHUser = _current_user  # type: ignore
