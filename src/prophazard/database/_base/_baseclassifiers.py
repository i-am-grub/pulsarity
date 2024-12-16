from sqlalchemy import UniqueConstraint, String, PickleType
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class _UserBase(AsyncAttrs, DeclarativeBase):
    """
    Base ORM Class with asynchronous attributes enabled for the user database
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    """Internal identifier"""
    _persistent: Mapped[bool] = mapped_column(name="persistent")
    """Entry is persistent in database"""


class _RaceBase(AsyncAttrs, DeclarativeBase):
    """
    Base ORM Class with asynchronous attributes enabled for the race database
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    """Internal identifier"""


class _RaceAttribute:
    """
    Attributes are simple storage variables which persist to the database and can
    be presented to users through frontend UI.
    """

    __table_args__ = (UniqueConstraint("id", "name"),)

    name: Mapped[str] = mapped_column(String(80), nullable=False, primary_key=True)
    """Name of attribute"""
    value: Mapped[str | int | float] = mapped_column(PickleType, nullable=True)
    """Value of attribute"""
