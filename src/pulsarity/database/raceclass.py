"""
ORM classes for race class data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Generic

from tortoise import fields
from tortoise.functions import Max

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import ATTRIBUTE
from pulsarity.database._base import PulsarityMessageBase as _PulsarityMessageBase
from pulsarity.database._base import PulsarityRaceBase as _PulsarityRaceBase

if TYPE_CHECKING:
    from pulsarity.database.raceevent import RaceEvent
    from pulsarity.database.raceformat import RaceFormat
    from pulsarity.database.round import Round


class RaceClassAttribute(_PulsarityMessageBase, Generic[ATTRIBUTE]):
    """
    Unique and stored individually stored values for each race class.
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass_attr"
        unique_together = (("raceclass", "name"),)

    name = fields.CharField(max_length=80)
    raceclass: fields.ForeignKeyRelation[RaceClass] = fields.ForeignKeyField(
        "event.RaceClass", related_name="attributes"
    )
    value = fields.JSONField[ATTRIBUTE]()

    def to_message(self) -> database_pb2.Attribute:
        return database_pb2.Attribute(name=self.name)


class RaceClass(_PulsarityRaceBase):
    """
    Database content for raceclasses
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass"
        unique_together = (("event", "raceclass_num"),)

    lock = asyncio.Lock()
    """Use when claiming a new `raceclass_num` during initial creation"""

    name_ = fields.CharField(max_length=120)
    """The name of the raceclass"""
    event: fields.ForeignKeyRelation[RaceEvent] = fields.ForeignKeyField(
        "event.RaceEvent", related_name="raceclasses"
    )
    """The event the raceclass is assigned to"""
    raceclass_num = fields.IntField()
    """The numerical identifier of the race class in the event"""
    rounds: fields.ReverseRelation[Round]
    """The rounds assigned to the race class"""
    raceformat: fields.ForeignKeyRelation[RaceFormat] = fields.ForeignKeyField(
        "event.RaceFormat"
    )
    attributes: fields.ReverseRelation[RaceClassAttribute]
    """The attributes assigned to the race class"""

    @property
    def name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name_:
            return self.name_

        return f"Race Class {self.id}"

    @property
    async def max_round_num(self) -> int | None:
        """
        Gets the maximum value number used as a `raceclass_num` in an events
        raceclasses
        """
        value = await self.rounds.all().annotate(max=Max("round_num")).first()

        if value is not None:
            return value.max  # type: ignore

        return None

    async def get_next_round_num(self) -> int:
        """
        The next recommend `raceclass_num` to use

        :return: The recommended integer
        """
        value = await self.max_round_num

        if value is None:
            return 1

        return value + 1

    def to_message(self) -> database_pb2.RaceClass:
        attrs = (attribute.to_message() for attribute in self.attributes)
        return database_pb2.RaceClass(id=self.id, name=self.name, attributes=attrs)

    @staticmethod
    def iterable_to_message(iterable) -> database_pb2.RaceClasses:
        raceclasses = (raceclasses.to_message() for raceclasses in iterable)
        return database_pb2.RaceClasses(raceclasses=raceclasses)
