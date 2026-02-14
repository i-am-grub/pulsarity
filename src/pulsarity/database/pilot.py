"""
ORM classes for Pilot data
"""

from __future__ import annotations

from typing import Iterable, Self

from pydantic import TypeAdapter
from tortoise import fields

from pulsarity._protobuf import database_pb2
from pulsarity.database._base import AttributeModel as _AttributeModel
from pulsarity.database._base import PulsarityBase as _PulsarityBase
from pulsarity.webserver.validation import ProtocolBufferModel

# pylint: disable=R0903,E1136


class PilotAttribute(_PulsarityBase):
    """
    Unique and stored individually stored values for each pilot.
    """

    name = fields.CharField(max_length=80)
    pilot: fields.ForeignKeyRelation[Pilot] = fields.ForeignKeyField(
        "event.Pilot", related_name="attributes"
    )

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "pilot_attr"
        unique_together = (("id", "name"),)


class Pilot(_PulsarityBase):
    """
    Database content for event participants
    """

    callsign = fields.CharField(max_length=80)
    """Pilot callsign"""
    phonetic = fields.CharField(max_length=80, null=True)
    """Phonetically-spelled callsign, used for text-to-speech"""
    name = fields.CharField(max_length=120, null=True)
    """Pilot name"""
    used_frequencies = fields.CharField(max_length=80, null=True)
    """Serialized list of frequencies this pilot has been assigned when starting a race, 
    ordered by recency"""
    attributes: fields.ReverseRelation[PilotAttribute]
    """PilotAttributes for this pilot. Access through awaitable attributes."""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "pilot"

    def __repr__(self):
        return f"<Pilot {self.id}>"

    @property
    def display_callsign(self) -> str:
        """
        Generates the displayed callsign for the user.

        :return: The user's displayed callsign
        """

        if self.callsign:
            return self.callsign

        if self.name:
            return self.name

        return f"Pilot {self.id}"

    @property
    def display_name(self) -> str:
        """
        Generates the displayed name for the user

        :return: The user's display name
        """
        if self.name:
            return self.name

        if self.callsign:
            return self.callsign

        return f"Pilot {self.id}"

    @property
    def spoken_callsign(self) -> str:
        """
        Generates the spoken callsign for the user

        :return: The user's spoken callsign
        """
        if self.phonetic:
            return self.phonetic

        if self.callsign:
            return self.callsign

        if self.name:
            return self.name

        return f"Pilot {self.id}"


class PilotModel(ProtocolBufferModel):
    """
    External Pilot model
    """

    id: int
    display_callsign: str
    display_name: str
    attributes: list[_AttributeModel]

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Pilot.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        attrs = (attribute.model_dump_protobuf() for attribute in self.attributes)
        return database_pb2.Pilot(
            id=self.id,
            display_callsign=self.display_callsign,
            display_name=self.display_callsign,
            attributes=attrs,
        )


_ADAPTER = TypeAdapter(list[PilotModel])


class PilotsModel(ProtocolBufferModel):
    """
    External Pilots model
    """

    pilots: list[PilotModel]

    @classmethod
    def from_iterable(cls, pilots: Iterable[Pilot]) -> Self:
        """
        Generates a validation model from a database iterable
        """
        return cls(pilots=_ADAPTER.validate_python(pilots, from_attributes=True))

    @classmethod
    def model_validate_protobuf(cls, data: bytes):
        message = database_pb2.Pilots.FromString(data)
        return cls.model_validate(message, from_attributes=True)

    def model_dump_protobuf(self):
        pilots = (pilot.model_dump_protobuf() for pilot in self.pilots)
        return database_pb2.Pilots(pilots=pilots)
