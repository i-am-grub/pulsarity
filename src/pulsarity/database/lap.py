"""
ORM classes for event data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase as _PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.slot import Slot

# pylint: disable=R0903,E1136


class LapAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each event.
    """

    name = fields.CharField(max_length=80)
    event: fields.ForeignKeyRelation[Lap] = fields.ForeignKeyField(
        "event.Lap", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "lap_attr"
        unique_together = (("id", "name"),)


class Lap(_PulsarityBase):
    """
    Database content for race laps
    """

    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField("event.Slot", "laps")
    """The slot the lap belongs to"""
    timedelta = fields.TimeDeltaField()
    """The time delta from race start"""
    timer_index = fields.IntField()
    """The index of the timer the lap was recorded from"""
    attributes: fields.ReverseRelation[LapAttribute]
    """The attributes assigned to the event"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "lap"
        unique_together = (("slot", "timedelta", "timer_index"),)
