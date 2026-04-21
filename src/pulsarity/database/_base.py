"""
Abstract definition of database classes
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Iterable, Self, TypeVar

from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from google.protobuf.message import Message

JsonParsable = bool | str | int | float | None
ATTRIBUTE = TypeVar("ATTRIBUTE", bound=JsonParsable)


class PulsarityBase(Model):
    """
    Base ORM Class for all database objects
    """

    id = fields.IntField(primary_key=True)
    """Internal identifier"""

    @classmethod
    async def get_by_id(cls, id_: int) -> Self | None:
        """
        Attempt to retrieve an object by its id

        :param id_: The id of the object to search for
        :return: The object from the database
        """
        return await cls.get_or_none(id=id_)


class PulsarityMessageBase(PulsarityBase):
    """
    An ABC Extention of `PulsarityBase` that includes a
    protocol buffer serialization method
    """

    @abstractmethod
    def to_message(self) -> Message:
        """
        Convert to protocol buffer structure
        """


class PulsarityRaceBase(PulsarityMessageBase):
    """
    An ABC Extention of `PulsarityMessageBase` that includes
    the ability to preload object attributes and convert
    iterables to protocol buffer messages
    """

    attributes: fields.ReverseRelation

    @classmethod
    async def get_by_id_with_attributes(cls, id_: int) -> Self | None:
        """
        Attempt to retrieve an object by its id

        :param id_: The id of the object to search for
        :return: The object from the database
        """
        return await cls.get_or_none(id=id_).select_related("attributes")

    @staticmethod
    @abstractmethod
    def iterable_to_message(iterable: Iterable[PulsarityRaceBase]) -> Message:
        """
        Convert iterable to protocol buffer structure
        """
