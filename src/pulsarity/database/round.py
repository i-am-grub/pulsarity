"""
ORM classes for round data
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
    from pulsarity.database.heat import Heat
    from pulsarity.database.raceclass import RaceClass


class RoundAttribute(_PulsarityMessageBase, Generic[ATTRIBUTE]):
    """
    Unique and stored individually stored values for each round.
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "round_attr"
        unique_together = (("round", "name"),)

    name = fields.CharField(max_length=80)
    round: fields.ForeignKeyRelation[Round] = fields.ForeignKeyField(
        "event.Round", related_name="attributes"
    )
    value = fields.JSONField[ATTRIBUTE]()

    def to_message(self) -> database_pb2.Attribute:
        return database_pb2.Attribute(name=self.name)


class Round(_PulsarityRaceBase):
    """
    Database content for rounds within a raceclass
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "round"
        unique_together = (("raceclass", "round_num"),)

    lock = asyncio.Lock()
    """Use when claiming a new `round_num` during initial creation"""

    raceclass: fields.ForeignKeyRelation[RaceClass] = fields.ForeignKeyField(
        "event.RaceClass", related_name="rounds"
    )
    """The class the round is assigned to"""
    round_num = fields.IntField(null=False)
    """The numerical identifier of the round in the raceclass"""
    heats: fields.ReverseRelation[Heat]
    """The heats assigned to the round"""
    attributes: fields.ReverseRelation[RoundAttribute]
    """The attributes assigned to the round"""

    @property
    async def max_heat_num(self) -> int | None:
        """
        Gets the maximum value number used as a `raceclass_num` in an events
        raceclasses
        """
        value = await self.heats.all().annotate(max=Max("heat_num")).first()

        if value is not None:
            return value.max  # type: ignore

        return None

    async def get_next_heat_num(self) -> int:
        """
        The next recommend `raceclass_num` to use

        :return: The recommended integer
        """
        value = await self.max_heat_num

        if value is None:
            return 1

        return value + 1

    def to_message(self) -> database_pb2.Round:
        attrs = (attr.to_message() for attr in self.attributes)
        return database_pb2.Round(
            id=self.id, round_num=self.round_num, attributes=attrs
        )

    @staticmethod
    def iterable_to_message(iterable) -> database_pb2.Rounds:
        rounds = (round_.to_message() for round_ in iterable)
        return database_pb2.Rounds(rounds=rounds)
