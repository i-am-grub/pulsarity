"""
ORM classes for Pilot data
"""

from __future__ import annotations

from tortoise import fields

from pulsarity.database._base import PulsarityBase

# pylint: disable=R0903,E1136


class PilotAttribute(PulsarityBase):
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


class Pilot(PulsarityBase):
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
    active = fields.BooleanField(default=True)
    """Not yet implemented"""
    attributes: fields.ReverseRelation[PilotAttribute]
    """PilotAttributes for this pilot. Access through awaitable attributes."""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "pilot"

    def __init__(
        self, *, name: str = "", callsign: str = "", phonetic: str = ""
    ) -> None:
        """
        Class initalizer

        :param name: _description_, defaults to ""
        :param callsign: _description_, defaults to ""
        :param phonetic: _description_, defaults to ""
        """
        super().__init__()

        self.name = name
        self.callsign = callsign
        self.phonetic = phonetic

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
