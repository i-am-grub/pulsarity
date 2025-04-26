"""
Abstract definition of database classes
"""

from typing import Self

from tortoise import fields
from tortoise.contrib.pydantic import (
    PydanticListModel,
    PydanticModel,
    pydantic_model_creator,
    pydantic_queryset_creator,
)
from tortoise.models import Model


class _PulsarityBase(Model):
    """
    Base ORM Class for all database objects
    """

    id = fields.IntField(primary_key=True)
    """Internal identifier"""

    @classmethod
    def generate_pydaantic_model(cls) -> type[PydanticModel]:
        """
        Generate a validation model for the database object

        :return: The generated model
        """
        return pydantic_model_creator(cls)

    @classmethod
    def generate_pydaantic_queryset(cls) -> type[PydanticListModel]:
        """
        Generate a validation model for the database object

        :return: The generated model
        """
        return pydantic_queryset_creator(cls)

    @classmethod
    async def get_by_id(cls, id_: int) -> Self | None:
        """
        Attempt to retrieve an object by its id

        :param session: _description_
        :param uuid: _description_
        :return: _description_
        """
        return await cls.get_or_none(id=id_)
