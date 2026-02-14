"""
ORM classes for heat data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterable, Self

from pydantic import TypeAdapter
from tortoise import fields

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import AttributeModel as _AttributeModel
from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.webserver.validation import ProtocolBufferModel

if TYPE_CHECKING:
    from pulsarity.database.round import Round
    from pulsarity.database.slot import Slot

# pylint: disable=R0903,E1136


class HeatAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each heat.
    """

    name = fields.CharField(max_length=80)
    heat: fields.ForeignKeyRelation[Heat] = fields.ForeignKeyField(
        "event.Heat", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "heat_attr"
        unique_together = (("id", "name"),)


class Heat(_PulsarityBase):
    """
    Database content for race heats
    """

    lock = asyncio.Lock()
    """Use when claiming a new `heat_num` during initial creation"""

    round: fields.ForeignKeyRelation[Round] = fields.ForeignKeyField(
        "event.Round", related_name="heats"
    )
    """The round the heat is assigned to"""
    heat_num = fields.IntField(null=False)
    """The numerical identifer of the heat within the round"""
    slots: fields.ReverseRelation[Slot]
    """The slots assigned to the heat"""
    completed = fields.BooleanField(default=False)
    """Whether the heat has been completed or not"""
    attributes: fields.ReverseRelation[HeatAttribute]
    """The attributes assigned to the heat"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "heat"
        unique_together = (("round", "heat_num"),)


class HeatModel(ProtocolBufferModel):
    """
    External heat model
    """

    id: int
    heat_num: int
    attributes: list[_AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Heat.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.Heat(id=self.id, heat_num=self.heat_num, attributes=attrs)


_ADAPTER = TypeAdapter(list[HeatModel])


class HeatsModel(ProtocolBufferModel):
    """
    External heats model
    """

    heats: list[HeatModel]

    @classmethod
    def from_iterable(cls, heats: Iterable[Heat]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(heats=_ADAPTER.validate_python(heats, from_attributes=True))

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.Heats.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.Heats:
        heats = (heat.model_dump_protobuf() for heat in self.heats)
        return database_pb2.Heats(heats=heats)
