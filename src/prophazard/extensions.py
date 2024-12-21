from asyncio import Future, get_running_loop
from uuid import UUID

from quart import Quart, Blueprint
from quart import current_app as _current_app
from quart_auth import AuthUser
from quart_auth import current_user as _current_user

from .events import EventBroker
from .database.user import UserDatabaseManager, User, UserPermission
from .database.race import RaceDatabaseManager


class RHApplication(Quart):
    """
    RotorHazard web application based on Quart
    """

    event_broker: EventBroker = EventBroker()
    _user_database: Future[UserDatabaseManager] | None = None
    _race_database: Future[RaceDatabaseManager] | None = None

    async def get_user_database(self) -> UserDatabaseManager:
        if self._user_database is None:
            loop = get_running_loop()
            self._user_database = loop.create_future()

        return await self._user_database

    def set_user_database(self, manager: UserDatabaseManager) -> None:
        if self._user_database is None:
            loop = get_running_loop()
            self._user_database = loop.create_future()

        self._user_database.set_result(manager)

    async def get_race_database(self) -> RaceDatabaseManager:
        if self._race_database is None:
            loop = get_running_loop()
            self._race_database = loop.create_future()

        return await self._race_database

    def set_race_database(self, manager: RaceDatabaseManager) -> None:
        if self._race_database is None:
            loop = get_running_loop()
            self._race_database = loop.create_future()

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
        session_maker = db_manager.new_session_maker()

        async with session_maker() as session:
            uuid = UUID(hex=self._auth_id)
            user: User | None = await db_manager.users.get_by_uuid(session, uuid)
            if user is None:
                return False

            permissions = await user.permissions
            if permission in permissions:
                return True
            else:
                return False


current_user: RHUser = _current_user  # type: ignore
