"""
ORM classes for heat data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.round import Round
    from pulsarity.database.slot import Slot

# pylint: disable=R0903,E1136


class HeatAttribute(PulsarityBase):
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


class Heat(PulsarityBase):
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
