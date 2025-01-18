"""
Abstract management of `_RaceBase` and `_UserBase` classes
"""

from typing import TypeVar, Generic, ParamSpec, Concatenate, Self
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, AsyncGenerator, Coroutine
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import make_transient
from sqlalchemy import ScalarResult, select, delete, func

from ._baseclassifiers import _UserBase, _RaceBase

T = TypeVar("T", bound=_RaceBase | _UserBase)
P = ParamSpec("P")
R = TypeVar("R")
U = TypeVar("U")


class _BaseManager(Generic[T], metaclass=ABCMeta):
    """
    The abstract class manager for all database objects
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """
        Class Initalization

        :param session_maker: The default session
        maker to use for the manager.
        """
        self._session_maker: async_sessionmaker[AsyncSession] = session_maker

    @property
    @abstractmethod
    def _table_class(self) -> type[T]:
        """
        Property holding the respective class type for the database object

        :raises NotImplementedError: Error flagging the property as abstract
        :return: Return type to use when overriding this method
        """
        raise NotImplementedError("This is an abstract method and should not be used")

    def optional_session(  # type: ignore
        function: Callable[Concatenate[Self, AsyncSession, P], Coroutine[None, None, R]]
    ) -> Callable[Concatenate[Self, AsyncSession | None, P], Coroutine[None, None, R]]:
        """
        Decorator to ensure there is a valid session for the async method
        if one isn't provided

        When using this decorator, the transaction will not be automatically
        commited when a session is provided.
        """
        # pylint: disable=E1102,E0213,W0212

        wraps(function)

        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> R:
            session: AsyncSession = args[0]  # type: ignore
            if session is not None:
                return await function(self, *args, **kwargs)  # type: ignore

            async with self._session_maker() as session:
                args_: tuple[AsyncSession, P.args] = (session, *args[1:])  # type: ignore
                results = await function(self, *args_, **kwargs)
                await session.commit()
                return results

        return wrapper  # type: ignore

    def optional_session_generator(  # type: ignore
        function: Callable[Concatenate[Self, AsyncSession, P], AsyncGenerator[R, U]]
    ) -> Callable[Concatenate[Self, AsyncSession | None, P], AsyncGenerator[R, U]]:
        """
        Decorator that mimics ensure_session for methods that create
        an `AsyncGenerator`

        When using this decorator, the transaction will not be automatically
        commited when a session is provided.
        """
        # pylint: disable=E1102,E0213,W0212

        wraps(function)

        async def wrapper(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncGenerator[R, U]:
            session: AsyncSession = args[0]  # type: ignore
            if session is not None:
                async for value in function(self, *args, **kwargs):  # type: ignore
                    yield value

            else:
                async with self._session_maker() as session:
                    args_: tuple[AsyncSession, P.args] = (session, *args[1:])  # type: ignore
                    async for value in function(self, *args_, **kwargs):
                        yield value
                    await session.commit()

        return wrapper  # type: ignore

    @optional_session
    async def num_entries(self, session: AsyncSession) -> int:
        """
        The number of entries in the table.

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :return int: The number of objects in the database table
        """
        # pylint: disable=E1102
        statement = func.count(self._table_class.id)
        result = await session.scalar(statement)
        return 0 if result is None else result

    @optional_session
    async def get_by_id(self, session: AsyncSession, obj_id: int) -> T | None:
        """
        Get an object from the database by id.

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :param id: Id of the object to retreive
        :return: Object from the database
        """
        statement = select(self._table_class).where(self._table_class.id == obj_id)
        return await session.scalar(statement)

    @optional_session
    async def get_all(self, session: AsyncSession) -> ScalarResult[T]:
        """
        Get all objects in the table from the database.

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :return: List of objects from the database
        """
        statement = select(self._table_class)
        return await session.scalars(statement)

    @optional_session_generator
    async def get_all_as_stream(self, session: AsyncSession) -> AsyncGenerator[T, None]:
        """
        Streams all objects in the tables from the database.

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :yield: Stream of objects from the database
        """
        statement = select(self._table_class)
        result = await session.stream_scalars(statement)
        async for scalar in result:
            yield scalar

    @optional_session
    async def add(self, session: AsyncSession, db_object: T | None = None) -> int:
        """
        Adds an object to the database. Adds a default object if one is not provided.

        :param session: Session to use for database transaction
        When providing a session, transactions **will not** be automatically commited.
        :param db_object: _description_, defaults to None
        :return: Id of the new
        """
        if db_object is None:
            db_object_ = self._table_class()
        else:
            db_object_ = db_object

        session.add(db_object_)
        await session.flush()

        return db_object_.id

    @optional_session
    async def add_many(
        self, session: AsyncSession, num_defaults: int, *db_objects: T
    ) -> list[int]:
        """
        Adds multiple objects to the database in a single transaction.

        :param session: Session to use for database transaction
        When providing a session, transactions **will not** be automatically commited.
        :param num_defaults: The number of defaults to add
        :param *db_objects: Predefined objects to add to the database
        :return: List of ids of the newly added objects
        """

        db_objects_ = db_objects + tuple(
            (self._table_class() for _ in range(num_defaults))
        )

        session.add_all(db_objects_)
        await session.flush()

        return [db_object.id for db_object in db_objects_]

    async def add_duplicate(self, session: AsyncSession, db_object: T) -> int:
        """
        Duplicates an instance of T. Must occur within the same session as when the
        original is pulled from the database.

        :param session: Session to use for database transaction
        :param db_object: Object to duplicate
        :return: Id of the newly created object
        """
        session.expunge(db_object)
        make_transient(db_object)
        del db_object.id

        return await self.add(session, db_object)

    @optional_session
    async def delete(self, session: AsyncSession, db_object: T) -> None:
        """
        Delete an object from the database. Persistent objects are not removed

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :param db_object: Object to delete from the database.
        """

        if isinstance(db_object, _UserBase) and db_object.persistent:
            return

        await session.delete(db_object)
        await session.flush()

    @optional_session
    async def clear_table(self, session: AsyncSession) -> None:
        """
        Clear all entries from the table. Persistent objects are not removed

        :param session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        """
        # pylint: disable=C0121

        if issubclass(self._table_class, _UserBase):
            statement = delete(self._table_class).where(
                self._table_class.persistent == False
            )
        else:
            statement = delete(self._table_class)

        await session.execute(statement)
        await session.flush()
