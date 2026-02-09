"""
ORM classes for event data
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Self

from google.protobuf import timestamp_pb2  # type: ignore
from pydantic import TypeAdapter
from tortoise import fields
from tortoise.functions import Max

from pulsarity.database._base import AttributeModel as _AttributeModel
from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.protobuf import database_pb2
from pulsarity.webserver.validation import ProtocolBufferModel

if TYPE_CHECKING:
    from pulsarity.database.raceclass import RaceClass

# pylint: disable=R0903,E1136


class RaceEventAttribute(_PulsarityBase):
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


class RaceEvent(_PulsarityBase):
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


_ATT_ADAPTER = TypeAdapter(list[_AttributeModel])


class RaceEventModel(ProtocolBufferModel):
    """
    External event model
    """

    id: int
    name: str
    date: datetime
    attributes: list[_AttributeModel]

    @classmethod
    def from_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceEvent.FromString(data)
        message.date = message.date.ToDatetime()
        model = cls(
            id=message.id,
            name=message.name,
            date=message.date.ToDatetime(),
            attributes=_ATT_ADAPTER.validate_python(message.attributes),
        )
        return cls.model_validate(model)

    def to_message(self) -> database_pb2.RaceEvent:
        attrs = (attribute.to_message() for attribute in self.attributes)
        date = timestamp_pb2.Timestamp()
        date.FromDatetime(self.date)
        return database_pb2.RaceEvent(
            id=self.id, name=self.name, date=date, attributes=attrs
        )


_ADAPTER = TypeAdapter(list[RaceEventModel])


class RaceEventsModel(ProtocolBufferModel):
    """
    External events model
    """

    events: list[RaceEventModel]

    @classmethod
    def from_iterable(cls, events: Iterable[RaceEvent]) -> Self:
        """
        Generates a validation model from a database iterable
        """

        return cls(events=_ADAPTER.validate_python(events, from_attributes=True))

    @classmethod
    def from_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceEvents.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def to_message(self) -> database_pb2.RaceEvents:
        events = (event.to_message() for event in self.events)
        return database_pb2.RaceEvents(events=events)
