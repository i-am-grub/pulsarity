"""
ORM classes for slot data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.database.pilot import Pilot

if TYPE_CHECKING:
    from pulsarity.database.heat import Heat
    from pulsarity.database.lap import Lap
    from pulsarity.database.signal import SignalHistory


# pylint: disable=R0903,E1136, E1101


class SlotAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each round.
    """

    name = fields.CharField(max_length=80)
    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField(
        "event.Slot", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot_attr"
        unique_together = (("id", "name"),)


class Slot(_PulsarityBase):
    """
    Database content for slots
    """

    heat: fields.ForeignKeyRelation[Heat] = fields.ForeignKeyField(
        "event.Heat", related_name="slots"
    )
    """The heat the slot belongs to"""
    index = fields.IntField(null=False)
    """The numerical indentifier of the slot in the heat"""
    pilot: fields.ForeignKeyRelation[Pilot] = fields.ForeignKeyField("event.Pilot")
    """The pilot assigned to the slot"""
    laps: fields.ReverseRelation[Lap]
    """The laps assigned to the slot"""
    history: fields.ReverseRelation[SignalHistory]
    """The slot's time series values for the race"""
    attributes: fields.ReverseRelation[SlotAttribute]
    """The custom attributes of the slot"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot"
        unique_together = (("heat", "index"), ("heat", "pilot"))
