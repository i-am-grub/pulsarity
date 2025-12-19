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

        :param session: _description_
        :param uuid: _description_
        :return: _description_
        """
        return await cls.get_or_none(id=id_)

    @classmethod
    async def get_by_id_with_attributes(cls, id_: int) -> Self | None:
        """
        Attempt to retrieve an object by its id

        :param session: _description_
        :param uuid: _description_
        :return: _description_
        """
        return await cls.get_or_none(id=id_).prefetch_related("attributes")


class AttributeModel(BaseModel):
    """
    External attributes model
    """

    name: str
