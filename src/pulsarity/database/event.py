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


class EventAttribute(PulsarityBase):
    """
    Unique and stored individually stored values for each event.
    """

    name = fields.CharField(max_length=80)
    event: fields.ForeignKeyRelation[Event] = fields.ForeignKeyField(
        "event.Event", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "event_attr"
        unique_together = (("id", "name"),)


class Event(PulsarityBase):
    """
    Database content for race events
    """

    name = fields.CharField(max_length=120)
    raceclasses: fields.ReverseRelation[RaceClass]
    """The race classes assigned to the event"""
    attributes: fields.ReverseRelation[EventAttribute]
    """The attributes assigned to the event"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "event"
