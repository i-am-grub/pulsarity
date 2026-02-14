"""
Abstract definition of database classes
"""

from typing import Self

from tortoise import fields
from tortoise.models import Model

from pulsarity.protobuf import database_pb2
from pulsarity.webserver.validation import ProtocolBufferModel


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


class AttributeModel(ProtocolBufferModel):
    """
    External attributes model
    """

    name: str

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Attribute.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        message = database_pb2.Attribute(name=self.name)
        return message.SerializeToString()
