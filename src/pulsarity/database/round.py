"""
ORM classes for round data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from pydantic import BaseModel, TypeAdapter
from tortoise import fields
from tortoise.functions import Max

from pulsarity.database._base import PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.heat import Heat
    from pulsarity.database.raceclass import RaceClass

# pylint: disable=R0903,E1136


class RoundAttribute(PulsarityBase):
    """
    Unique and stored individually stored values for each round.
    """

    name = fields.CharField(max_length=80)
    raceclass: fields.ForeignKeyRelation[Round] = fields.ForeignKeyField(
        "event.Round", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "round_attr"
        unique_together = (("id", "name"),)


class Round(PulsarityBase):
    """
    Database content for rounds within a raceclass
    """

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

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "round"
        unique_together = (("raceclass", "round_num"),)

    @property
    async def max_heat_num(self) -> int | None:
        """
        Gets the maximum value number used as a `raceclass_num` in an events
        raceclasses
        """
        value = await self.heats.all().annotate(max=Max("heat_num")).first()

        if value is not None:
            return getattr(value, "max")

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


class _RoundModel(BaseModel):
    """
    External round model
    """

    id: int


RoundAdapter = TypeAdapter(_RoundModel)
RoundListAdapter = TypeAdapter(list[_RoundModel])
