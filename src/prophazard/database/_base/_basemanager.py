from typing import TypeVar, Generic, ParamSpec, Concatenate, Self
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, AsyncGenerator, Coroutine

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

        :param async_sessionmaker[AsyncSession] session_maker: _description_
        """
        self._session_maker: async_sessionmaker[AsyncSession] = session_maker

    @property
    @abstractmethod
    def _table_class(self) -> type[T]:
        """
        Property holding the respective class type for the database object

        :raises NotImplementedError: Error flagging the property as abstract
        :return Type[T]: Return type to use when overriding this method
        """
        raise NotImplementedError("This is an abstract method and should not be used")

    def _optional_session(  # type: ignore
        func: Callable[Concatenate[Self, AsyncSession, P], Coroutine[None, None, R]]
    ) -> Callable[Concatenate[Self, AsyncSession | None, P], Coroutine[None, None, R]]:
        """
        Decorator to ensure there is a valid session for the async method
        if one isn't provided

        When using this decorator, the transaction will not be automatically
        commited when a session is provided.
        """

        async def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> R:
            session: AsyncSession = args[0]  # type: ignore
            if session is not None:
                return await func(self, *args, **kwargs)  # type: ignore

            else:
                async with self._session_maker() as session:
                    args = (session, *args[1:])
                    results = await func(self, *args, **kwargs)
                    await session.commit()
                    return results

        return wrapper  # type: ignore

    def _optional_session_generator(  # type: ignore
        func: Callable[Concatenate[Self, AsyncSession, P], AsyncGenerator[R, U]]
    ) -> Callable[Concatenate[Self, AsyncSession | None, P], AsyncGenerator[R, U]]:
        """
        Decorator that mimics ensure_session for methods that create
        an `AsyncGenerator`

        When using this decorator, the transaction will not be automatically
        commited when a session is provided.
        """

        async def wrapper(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncGenerator[R, U]:
            session: AsyncSession = args[0]  # type: ignore
            if session is not None:
                async for value in func(self, *args, **kwargs):  # type: ignore
                    yield value

            else:
                async with self._session_maker() as session:
                    args = (session, *args[1:])
                    async for value in func(self, *args, **kwargs):
                        yield value
                    await session.commit()

        return wrapper  # type: ignore

    @_optional_session
    async def num_entries(self, session: AsyncSession) -> int:
        """
        Counts the number of entries in the table.

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :return int: The number of objects in the database table
        """
        statement = func.count(self._table_class.id)
        result = await session.scalar(statement)
        return 0 if result is None else result

    @_optional_session
    async def get_by_id(self, session: AsyncSession, id: int) -> T | None:
        """
        _summary_

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :param int id: Id of the object to retreive
        :return T | None: Object from the database
        """
        statement = select(self._table_class).where(self._table_class.id == id)
        return await session.scalar(statement)

    @_optional_session
    async def get_all(self, session: AsyncSession) -> ScalarResult[T]:
        """
        _summary_

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :return ScalarResult[T]: List of objects from the database
        """
        statement = select(self._table_class)
        return await session.scalars(statement)

    @_optional_session_generator
    async def get_all_as_stream(self, session: AsyncSession) -> AsyncGenerator[T, None]:
        """
        _summary_

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :yield AsyncGenerator[T,None]: Stream of objects from the database
        """
        statement = select(self._table_class)
        result = await session.stream_scalars(statement)
        async for scalar in result:
            yield scalar

    @_optional_session
    async def add(self, session: AsyncSession, db_object: T | None = None) -> int:
        """
        Adds an object to the database. Adds a default object if one is not provided.

        :param AsyncSession | None session: Session to use for database transaction
        When providing a session, transactions **will not** be automatically commited.
        :param T | None db_object: _description_, defaults to None
        :return int: Id of the new
        """
        if db_object is None:
            _db_object = self._table_class()
        else:
            _db_object = db_object

        session.add(_db_object)
        await session.flush()

        return _db_object.id

    @_optional_session
    async def add_many(
        self, session: AsyncSession, num_defaults: int, *db_objects: T
    ) -> list[int]:
        """
        _summary_

        :param AsyncSession | None session: Session to use for database transaction
        When providing a session, transactions **will not** be automatically commited.
        :param int num_defaults: The number of defaults to add
        :param T *db_objects: Objects to add to the database
        :return list[int]: List of ids of the newly added objects
        """

        _db_objects = db_objects + tuple(
            (self._table_class() for _ in range(num_defaults))
        )

        session.add_all(_db_objects)
        await session.flush()

        return [db_object.id for db_object in _db_objects]

    async def add_duplicate(self, session: AsyncSession, db_object: T) -> int:
        """
        Duplicates an instance of T. Must occur within the same session as when the
        original is pulled from the database.

        :param AsyncSession session: Session to use for database transaction
        :param T db_object: Object to duplicate
        :return int: Id of the newly created object
        """
        session.expunge(db_object)
        make_transient(db_object)
        del db_object.id

        return await self.add(session, db_object)

    @_optional_session
    async def delete(self, session: AsyncSession, db_object: T) -> None:
        """
        Delete an object from the database

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        :param T db_object: Object to delete from the database.
        """
        await session.delete(db_object)
        await session.flush()

    @_optional_session
    async def clear_table(self, session: AsyncSession) -> None:
        """
        Clear all database entries from the table.

        :param AsyncSession | None session: Session to use for database transaction.
        When providing a session, transactions **will not** be automatically commited.
        """
        statement = delete(self._table_class)
        await session.execute(statement)
        await session.flush()
