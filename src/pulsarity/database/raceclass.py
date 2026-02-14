"""
ORM classes for race class data
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterable, Self

from pydantic import TypeAdapter
from tortoise import fields
from tortoise.functions import Max

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import AttributeModel as _AttributeModel
from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.webserver.validation import ProtocolBufferModel

if TYPE_CHECKING:
    from pulsarity.database.raceevent import RaceEvent
    from pulsarity.database.raceformat import RaceFormat
    from pulsarity.database.round import Round

# pylint: disable=R0903,E1136


class RaceClassAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each race class.
    """

    name = fields.CharField(max_length=80)
    raceclass: fields.ForeignKeyRelation[RaceClass] = fields.ForeignKeyField(
        "event.RaceClass", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass_attr"
        unique_together = (("id", "name"),)


class RaceClass(_PulsarityBase):
    """
    Database content for raceclasses
    """

    lock = asyncio.Lock()
    """Use when claiming a new `raceclass_num` during initial creation"""

    name_ = fields.CharField(max_length=120)
    """The name of the raceclass"""
    event: fields.ForeignKeyRelation[RaceEvent] = fields.ForeignKeyField(
        "event.RaceEvent", related_name="raceclasses"
    )
    """The event the raceclass is assigned to"""
    raceclass_num = fields.IntField()
    """The numerical identifier of the race class in the event"""
    rounds: fields.ReverseRelation[Round]
    """The rounds assigned to the race class"""
    raceformat: fields.ForeignKeyRelation[RaceFormat] = fields.ForeignKeyField(
        "event.RaceFormat"
    )
    attributes: fields.ReverseRelation[RaceClassAttribute]
    """The attributes assigned to the race class"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "raceclass"
        unique_together = (("event", "raceclass_num"),)

    @property
    def name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name_:
            return self.name_

        return f"Race Class {self.id}"

    @property
    async def max_round_num(self) -> int | None:
        """
        Gets the maximum value number used as a `raceclass_num` in an events
        raceclasses
        """
        value = await self.rounds.all().annotate(max=Max("round_num")).first()

        if value is not None:
            return getattr(value, "max")

        return None

    async def get_next_round_num(self) -> int:
        """
        The next recommend `raceclass_num` to use

        :return: The recommended integer
        """
        value = await self.max_round_num

        if value is None:
            return 1

        return value + 1


class RaceClassModel(ProtocolBufferModel):
    """
    External raceclass model
    """

    id: int
    name: str
    attributes: list[_AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceClass.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceClass:
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.RaceClass(id=self.id, name=self.name, attributes=attrs)


_ADAPTER = TypeAdapter(list[RaceClassModel])


class RaceClassesModel(ProtocolBufferModel):
    """
    External raceclasses model
    """

    raceclasses: list[RaceClassModel]

    @classmethod
    def from_iterable(cls, raceclasses: Iterable[RaceClass]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(
            raceclasses=_ADAPTER.validate_python(raceclasses, from_attributes=True)
        )

    @classmethod
    def model_validate_protobuf(cls, data: bytes) -> Self:
        message = database_pb2.RaceClasses.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self) -> database_pb2.RaceClasses:
        raceclasses = (
            raceclass.model_dump_protobuf() for raceclass in self.raceclasses
        )
        return database_pb2.RaceClasses(raceclasses=raceclasses)
