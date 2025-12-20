"""
Abstract definition of database classes
"""

from typing import Self

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model


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

    @classmethod
    async def get_by_id_with_attributes(cls, id_: int) -> Self | None:
        """
        Attempt to retrieve an object by its id

        :param id_: The id of the object to search for
        :return: The object from the database
        """
        return await cls.get_or_none(id=id_).prefetch_related("attributes")


class AttributeModel(BaseModel):
    """
    External attributes model
    """

    name: str
