"""
ORM classes for round data
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, TypeAdapter
from tortoise import fields

from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.database.pilot import Pilot

if TYPE_CHECKING:
    from pulsarity.database.heat import Heat
    from pulsarity.database.lap import Lap


# pylint: disable=R0903,E1136, E1101


class SlotAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each round.
    """

    name = fields.CharField(max_length=80)
    raceclass: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField(
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
    attributes: fields.ReverseRelation[SlotAttribute]
    """The custom attributes of the slot"""
    history: fields.BackwardOneToOneRelation[SlotHistory]
    """The slot's time series values for the race"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot"
        unique_together = (("heat", "index"), ("heat", "pilot"))


class SlotHistoryRecord(BaseModel):
    """
    Slot history entry
    """

    time: timedelta
    value: float

    def __lt__(self, obj: Self) -> bool:
        """
        Less than operation definition. Allows for sorting instances by time.
        """
        return self.time < obj.time


_SLOT_HISTORY_ADAPTER = TypeAdapter(tuple[SlotHistoryRecord, ...])


def history_encoder(history_series: Sequence[SlotHistoryRecord]) -> str:
    """
    Encodes a time series sequence to a storable value

    :param history_series: The history series sequence
    :return: The formated time series
    """
    data = _SLOT_HISTORY_ADAPTER.validate_python(history_series)
    return _SLOT_HISTORY_ADAPTER.dump_json(data).decode("utf-8")


class SlotHistory(_PulsarityBase):
    """
    Time series context for slot
    """

    slot: fields.OneToOneRelation[Slot] = fields.OneToOneField("event.Slot", "history")
    """The slot the history belongs to"""
    history: fields.JSONField[Sequence[SlotHistoryRecord]] = fields.JSONField(
        history_encoder,
        _SLOT_HISTORY_ADAPTER.validate_python,
    )  # type: ignore
    """The series of history for the slot"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot_history"
