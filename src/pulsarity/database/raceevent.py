"""
ORM classes for event data
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, TypeAdapter
from tortoise import fields
from tortoise.functions import Max

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

    name_ = fields.CharField(max_length=120)
    """The name of the event"""
    date = fields.DatetimeField(auto_now_add=True)
    """The date of the event"""
    raceclasses: fields.ReverseRelation["RaceClass"]
    """The race classes assigned to the event"""
    attributes: fields.ReverseRelation[RaceEventAttribute]
    """The attributes assigned to the event"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceevent"

    @property
    def name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name_ is not None:
            return self.name_

        return f"RaceEvent {self.id}"

    @property
    async def max_raceclass_num(self) -> int | None:
        """
        Gets the maximum value number used as a `raceclass_num` in an events
        raceclasses
        """
        value = await self.raceclasses.all().annotate(max=Max("raceclass_num")).first()

        if value is not None:
            return getattr(value, "max")

        return None

    async def get_next_raceclass_num(self) -> int:
        """
        The next recommend `raceclass_num` to use

        :return: The recommended integer
        """
        value = await self.max_raceclass_num

        if value is None:
            return 1

        return value + 1

    def __lt__(self, obj: Self) -> bool:
        """
        Less than comparsion operator. Enables sorting by dates
        """
        return self.date < obj.date


class _RaceEventModel(BaseModel):
    """
    External Event model
    """

    id: int
    name: str
    date: datetime


RACE_EVENT_ADAPTER = TypeAdapter(_RaceEventModel)
RACE_EVENT_LIST_ADAPTER = TypeAdapter(list[_RaceEventModel])
