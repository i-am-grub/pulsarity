"""
ORM classes for round data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

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
