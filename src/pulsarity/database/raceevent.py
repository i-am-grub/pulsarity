"""
ORM classes for event data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self

from google.protobuf import timestamp_pb2
from tortoise import fields
from tortoise.functions import Max

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import ATTRIBUTE
from pulsarity.database._base import PulsarityMessageBase as _PulsarityMessageBase
from pulsarity.database._base import PulsarityRaceBase as _PulsarityRaceBase

if TYPE_CHECKING:
    from pulsarity.database.raceclass import RaceClass


class RaceEventAttribute(_PulsarityMessageBase, Generic[ATTRIBUTE]):
    """
    Unique and stored individually stored values for each event.
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceevent_attr"
        unique_together = (("event", "name"),)

    name = fields.CharField(max_length=80)
    event: fields.ForeignKeyRelation[RaceEvent] = fields.ForeignKeyField(
        "event.RaceEvent", related_name="attributes"
    )
    value = fields.JSONField[ATTRIBUTE]()

    def to_message(self) -> database_pb2.Attribute:
        return database_pb2.Attribute(name=self.name)


class RaceEvent(_PulsarityRaceBase):
    """
    Database content for race events
    """

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceevent"

    name_ = fields.CharField(max_length=120)
    """The name of the event"""
    date = fields.DatetimeField(auto_now_add=True)
    """The date of the event"""
    raceclasses: fields.ReverseRelation["RaceClass"]
    """The race classes assigned to the event"""
    attributes: fields.ReverseRelation[RaceEventAttribute]
    """The attributes assigned to the event"""

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
            return value.max  # type: ignore

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

    def to_message(self) -> database_pb2.RaceEvent:
        attrs = (attribute.to_message() for attribute in self.attributes)
        date = timestamp_pb2.Timestamp()
        date.FromDatetime(self.date)
        return database_pb2.RaceEvent(
            id=self.id, name=self.name, date=date, attributes=attrs
        )

    @staticmethod
    def iterable_to_message(iterable) -> database_pb2.RaceEvents:
        """
        Convert iterable to protocol buffer structure
        """
        evts = (evt.to_message() for evt in iterable)
        return database_pb2.RaceEvents(events=evts)
