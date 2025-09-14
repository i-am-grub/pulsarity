"""
ORM classes for event data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.raceclass import RaceClass

# pylint: disable=R0903,E1136


class RaceEventAttribute(PulsarityBase):
    """
    Unique and stored individually stored values for each event.
    """

    name = fields.CharField(max_length=80)
    event: fields.ForeignKeyRelation[RaceEvent] = fields.ForeignKeyField(
        "event.RaceEvent", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceevent_attr"
        unique_together = (("id", "name"),)


class RaceEvent(PulsarityBase):
    """
    Database content for race events
    """

    name = fields.CharField(max_length=120)
    """The name of the event"""
    raceclasses: fields.ReverseRelation[RaceClass]
    """The race classes assigned to the event"""
    attributes: fields.ReverseRelation[RaceEventAttribute]
    """The attributes assigned to the event"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceevent"

    @property
    def display_name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name:
            return self.name

        return f"RaceEvent {self.id}"
