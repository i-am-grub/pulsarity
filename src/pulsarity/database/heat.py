"""
ORM classes for heat data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Generic

from tortoise import fields

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import ATTRIBUTE
from pulsarity.database._base import PulsarityMessageBase as _PulsarityMessageBase
from pulsarity.database._base import PulsarityRaceBase as _PulsarityRaceBase

if TYPE_CHECKING:
    from pulsarity.database.round import Round
    from pulsarity.database.slot import Slot


class HeatAttribute(_PulsarityMessageBase, Generic[ATTRIBUTE]):
    """
    Unique and stored individually stored values for each heat.
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "heat_attr"
        unique_together = (("heat", "name"),)

    name = fields.CharField(max_length=80)
    heat: fields.ForeignKeyRelation[Heat] = fields.ForeignKeyField(
        "event.Heat", related_name="attributes"
    )
    value = fields.JSONField[ATTRIBUTE]()

    def to_message(self) -> database_pb2.Attribute:
        return database_pb2.Attribute(name=self.name)


class Heat(_PulsarityRaceBase):
    """
    Database content for race heats
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "heat"
        unique_together = (("round", "heat_num"),)

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

    def to_message(self) -> database_pb2.Heat:
        attrs = (attr.to_message() for attr in self.attributes)
        return database_pb2.Heat(id=self.id, heat_num=self.heat_num, attributes=attrs)

    @staticmethod
    def iterable_to_message(iterable):
        heats = (heat.to_message() for heat in iterable)
        return database_pb2.Heats(heats=heats)
