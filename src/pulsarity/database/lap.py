"""
ORM classes for event data
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING

from tortoise import fields

from pulsarity.database._base import PulsarityBase

if TYPE_CHECKING:
    from pulsarity.database.slot import Slot

# pylint: disable=R0903,E1136


class LapKind(IntEnum):
    """
    The type of saved lap
    """

    PRIMARY = auto()
    """Lap from the primary timer"""
    SPLIT = auto()
    """Lap from a split timer"""


class LapAttribute(PulsarityBase):
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


class Lap(PulsarityBase):
    """
    Database content for race laps
    """

    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField("event.Slot", "laps")
    """The slot the lap belongs to"""
    time = fields.TimeDeltaField()
    """The time delta from race start"""
    kind = fields.IntEnumField(LapKind)
    """The lap kind"""
    attributes: fields.ReverseRelation[LapAttribute]
    """The attributes assigned to the event"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "lap"
