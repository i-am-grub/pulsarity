"""
Race database interaction
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ..._base import _RaceBase
from ._pilotmanager import _PilotManager


class RaceDatabaseManager:
    """
    Database manager for race related objects
    """

    def __init__(self, *, filename: str = ":memory:") -> None:
        """
        Class initializer

        :param _type_ filename: The filename to save the database as, defaults to ":memory:"
        """

        self.engine = create_async_engine(f"sqlite+aiosqlite:///{filename}", echo=False)
        default_session_maker = self.new_session_maker()

        self.pilots = _PilotManager(default_session_maker)
        """A """

    async def sync_database(self) -> None:
        """
        Setup the database connection. Used at server startup.
        """

        async with self.engine.begin() as conn:
            await conn.run_sync(_RaceBase.metadata.create_all)

    async def shutdown(self) -> None:
        """
        Shutdown the database connection.
        """

        await self.engine.dispose()

    def new_session_maker(self, **kwargs) -> async_sessionmaker[AsyncSession]:
        """
        A wrapper for async_sessionmaker with `autoflush`, `autocommit`, and
        `expire_on_commit` set to `False`. Automatically set the engine

        :return async_sessionmaker[AsyncSession]: _description_
        """
        kwargs["autoflush"] = False
        kwargs["autocommit"] = False
        kwargs["expire_on_commit"] = False

        return async_sessionmaker(self.engine, **kwargs)
