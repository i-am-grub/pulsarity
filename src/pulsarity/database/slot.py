"""
ORM classes for round data
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Self

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


@dataclass(frozen=True)
class SlotHistoryRecord:
    """
    Slot history entry
    """

    time: timedelta
    value: float

    @classmethod
    def from_sequence(cls, data: Sequence[float]) -> Self:
        """
        Parses a record from a sequence
        """
        delta = timedelta(seconds=data[0])
        return cls(time=delta, value=data[1])

    def __lt__(self, obj: Self) -> bool:
        """
        Less than operation definition. Allows for sorting instances by time.
        """
        return self.time < obj.time


def history_encoder(history_series: Sequence[SlotHistoryRecord]) -> str:
    """
    Encodes a time series sequence to a storable value

    :param history_series: The history series sequence
    :return: The formated time series
    """
    data = [(x.time.total_seconds(), x.value) for x in history_series]
    return json.dumps(data)


def history_decoder(encoded_data: str | bytes) -> tuple[SlotHistoryRecord, ...]:
    """
    Decodes a time series sequence from a storable value

    :param history_series: The encoded data
    :return: The sequence of records
    """
    data: list[list[float]] = json.loads(encoded_data)
    return tuple(SlotHistoryRecord.from_sequence(x) for x in data)


class SlotHistory(_PulsarityBase):
    """
    Time series context for slot
    """

    slot: fields.OneToOneRelation[Slot] = fields.OneToOneField("event.Slot", "history")
    """The slot the history belongs to"""
    history: fields.JSONField[tuple[SlotHistoryRecord, ...]] = fields.JSONField(
        history_encoder, history_decoder
    )  # type: ignore
    """The series of history for the slot"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "slot_history"
