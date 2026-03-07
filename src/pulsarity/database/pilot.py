"""
ORM classes for Pilot data
"""

from __future__ import annotations

from typing import Generic

from tortoise import fields

from pulsarity.database._base import ATTRIBUTE
from pulsarity.database._base import PulsarityBase as _PulsarityBase


class PilotAttribute(_PulsarityBase, Generic[ATTRIBUTE]):
    """
    Unique and stored individually stored values for each pilot.
    """

    name = fields.CharField(max_length=80)
    pilot: fields.ForeignKeyRelation[Pilot] = fields.ForeignKeyField(
        "event.Pilot", related_name="attributes"
    )
    value = fields.JSONField[ATTRIBUTE]()

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "pilot_attr"
        unique_together = (("pilot", "name"),)


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
