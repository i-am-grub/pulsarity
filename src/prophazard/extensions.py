"""
Modules extended from Quart and some of its
extentions.
"""

import sys
import asyncio
import logging
from uuid import UUID
from typing import Any
from collections.abc import Callable

from quart import Quart, Blueprint
from quart import current_app as _current_app
from quart_auth import AuthUser
from quart_auth import current_user as _current_user

from .events import EventBroker
from .database.user import UserDatabaseManager, User, UserPermission
from .database.race import RaceDatabaseManager
from .race.manager import RaceManager

logger = logging.getLogger(__name__)


class RHApplication(Quart):
    """
    RotorHazard web application based on Quart
    """

    # pylint: disable=W0106

    _user_database: asyncio.Future[UserDatabaseManager] | None = None
    _race_database: asyncio.Future[RaceDatabaseManager] | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__.__doc__
        super().__init__(*args, **kwargs)

        self.event_broker: EventBroker = EventBroker()
        self.race_manager: RaceManager = RaceManager()

    async def get_user_database(self) -> UserDatabaseManager:
        """
        Gets the user database for the application. Waits for
        it to be set if needed.

        :return: The user database
        """
        if self._user_database is None:
            loop = asyncio.get_running_loop()
            self._user_database = loop.create_future()

        return await self._user_database

    def set_user_database(self, manager: UserDatabaseManager) -> None:
        """
        Sets the user database.

        :param manager: The user database to set
        """
        if self._user_database is None:
            loop = asyncio.get_running_loop()
            self._user_database = loop.create_future()

        self._user_database.set_result(manager)

    async def get_race_database(self) -> RaceDatabaseManager:
        """
        Gets the race database for the application. Waits for
        it to be set if needed.

        :return: The race database
        """
        if self._race_database is None:
            loop = asyncio.get_running_loop()
            self._race_database = loop.create_future()

        return await self._race_database

    def set_race_database(self, manager: RaceDatabaseManager) -> None:
        """
        Sets the race database.

        :param manager: The race database to set
        """
        if self._race_database is None:
            loop = asyncio.get_running_loop()
            self._race_database = loop.create_future()

        self._race_database.set_result(manager)

    def schedule_background_task(
        self, time: float, func: Callable, *args: Any, **kwargs: Any
    ) -> asyncio.TimerHandle:
        """
        Schedules a background task to occur at a specific time with
        app context. The task will be generated as an eager task if
        possible and block the event loop slightly before it is
        scheduled to attempt to be as accurate as possible.

        :param time: The event loop time to schedule the task for
        :param func: The function to schedule

        :return: The schedule timer handler
        """
        # pylint: disable= W0718

        async def _wrapper() -> None:
            try:
                async with self.app_context():
                    await self.ensure_async(func)(*args, **kwargs)
            except Exception as error:
                await self.handle_background_exception(error)

        def _create_task() -> None:

            while (time_ := loop.time() - time) < 0:
                pass

            if sys.version_info >= (3, 12):
                task = asyncio.eager_task_factory(loop, _wrapper())
            else:
                task = asyncio.create_task(_wrapper())

            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

            logger.debug(
                "Task scheduled for %s, running at %s", f"{time:.3f}", f"{time_:.3f}"
            )

        loop = asyncio.get_running_loop()

        if time < loop.time():
            raise ValueError("Scheduled time is in the past")

        return loop.call_at(time - 0.05, _create_task)

    def delay_background_task(
        self, delay: float, func: Callable, *args: Any, **kwargs: Any
    ) -> asyncio.TimerHandle:
        """
        Schedules a task to be ran x seconds in the future. See `schedule_background_task`
        for more information.

        :param delay: Amount of seconds in the future to schdule the task
        :param fuction: The function to schedule
        :return: The schedule timer handler
        """
        loop = asyncio.get_running_loop()
        time = loop.time() + delay
        return self.schedule_background_task(time, func, *args, **kwargs)


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

    async def get_permissions(self) -> set[str]:
        """
        Get the permissions for the user

        :return: The set of permissions
        """

        if self._auth_id is None:
            return set()

        db_manager = await current_app.get_user_database()
        session_maker = db_manager.new_session_maker()

        async with session_maker() as session:
            uuid = UUID(hex=self._auth_id)
            user: User | None = await db_manager.users.get_by_uuid(session, uuid)
            if user is None:
                return set()

            return await user.permissions

    async def has_permission(self, permission: UserPermission) -> bool:
        """
        Check a user for valid permissions

        :param permission: The user permission to check for
        :return: Status of the user have the permission. Returning
        True verifies that the permission has been granted.
        """

        permissions = await self.get_permissions()
        return permission in permissions


current_user: RHUser = _current_user  # type: ignore
