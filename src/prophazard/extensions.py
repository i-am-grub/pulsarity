"""
Modules extended from Quart and some of its
extentions.
"""

from asyncio import Future, get_running_loop
from uuid import UUID

from quart import Quart, Blueprint
from quart import current_app as _current_app
from quart_auth import AuthUser
from quart_auth import current_user as _current_user

from .events import EventBroker
from .database.user import UserDatabaseManager, User, UserPermission
from .database.race import RaceDatabaseManager
from .race.manager import RaceManager


class RHApplication(Quart):
    """
    RotorHazard web application based on Quart
    """

    event_broker: EventBroker = EventBroker()
    race_manager: RaceManager = RaceManager()
    _user_database: Future[UserDatabaseManager] | None = None
    _race_database: Future[RaceDatabaseManager] | None = None

    async def get_user_database(self) -> UserDatabaseManager:
        """
        Gets the user database for the application. Waits for
        it to be set if needed.

        :return UserDatabaseManager: The user database
        """
        if self._user_database is None:
            loop = get_running_loop()
            self._user_database = loop.create_future()

        return await self._user_database

    def set_user_database(self, manager: UserDatabaseManager) -> None:
        """
        Sets the user database.

        :param UserDatabaseManager manager: The user database to set
        """
        if self._user_database is None:
            loop = get_running_loop()
            self._user_database = loop.create_future()

        self._user_database.set_result(manager)

    async def get_race_database(self) -> RaceDatabaseManager:
        """
        Gets the race database for the application. Waits for
        it to be set if needed.

        :return RaceDatabaseManager: The race database
        """
        if self._race_database is None:
            loop = get_running_loop()
            self._race_database = loop.create_future()

        return await self._race_database

    def set_race_database(self, manager: RaceDatabaseManager) -> None:
        """
        Sets the race database.

        :param RaceDatabaseManager manager: The race database to set
        """
        if self._race_database is None:
            loop = get_running_loop()
            self._race_database = loop.create_future()

        self._race_database.set_result(manager)


class RHBlueprint(Blueprint):
    """
    RotorHazard Quart based blueprints
    """


current_app: RHApplication = _current_app  # type: ignore


class RHUser(AuthUser):
    """
    The client user class for system authentication and guarding access
    to routes and websockets.
    """

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
            return permission in permissions


current_user: RHUser = _current_user  # type: ignore
