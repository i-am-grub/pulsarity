"""
ORM classes for race class data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.raceevent import RaceEvent
    from pulsarity.database.raceformat import RaceFormat
    from pulsarity.database.round import Round

# pylint: disable=R0903,E1136


class RaceClassAttribute(PulsarityBase):
    """
    Unique and stored individually stored values for each race class.
    """

    name = fields.CharField(max_length=80)
    raceclass: fields.ForeignKeyRelation[RaceClass] = fields.ForeignKeyField(
        "event.RaceClass", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass_attr"
        unique_together = (("id", "name"),)


class RaceClass(PulsarityBase):
    """
    Database content for raceclasses
    """

    name = fields.CharField(max_length=120)
    """The name of the raceclass"""
    event: fields.ForeignKeyRelation[RaceEvent] = fields.ForeignKeyField(
        "event.RaceEvent", related_name="raceclasses"
    )
    """The event the raceclass is assigned to"""
    raceclass_num = fields.IntField(null=False)
    """The numerical identifier of the race class in the event"""
    rounds: fields.ReverseRelation[Round]
    """The rounds assigned to the race class"""
    raceformat: fields.ForeignKeyRelation[RaceFormat] = fields.ForeignKeyField(
        "event.RaceFormat"
    )
    attributes: fields.ReverseRelation[RaceClassAttribute]
    """The attributes assigned to the race class"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass"
        unique_together = (("event", "raceclass_num"),)

    @property
    def display_name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name:
            return self.name

        return f"Race Class {self.id}"
