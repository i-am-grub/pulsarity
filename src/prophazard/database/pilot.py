"""
ORM classes for Pilot data
"""

from __future__ import annotations

from tortoise import fields

from .base import _PHDataBase

# pylint: disable=E1136


class PilotAttribute(_PHDataBase):
    """
    Unique and stored individually stored values for each pilot.
    """

    # pylint: disable=R0903

    name = fields.CharField(max_length=80)
    pilot_id: fields.ForeignKeyRelation[Pilot] = fields.ForeignKeyField(
        "models.Pilot", related_name="id"
    )

    class Meta:
        """Tortoise ORM metadata"""

        table = "pilot_attr"
        unique_together = (("id", "name"),)


class Pilot(_PHDataBase):
    """
    A pilot is an individual participant. In order to participate in races,
    pilots can be assigned to multiple heats.

    The sentinel value :atts:`RHUtils.PILOT_ID_NONE` should be used when no pilot is defined.
    """

    __tablename__ = "pilot"

    callsign = fields.CharField(max_length=80)
    """Pilot callsign"""
    phonetic = fields.CharField(max_length=80)
    """Phonetically-spelled callsign, used for text-to-speech"""
    name = fields.CharField(max_length=120)
    """Pilot name"""
    used_frequencies = fields.CharField(max_length=80, null=True)
    """Serialized list of frequencies this pilot has been assigned when starting a race, 
    ordered by recency"""
    active = fields.BooleanField(default=True)
    """Not yet implemented"""
    attributes: fields.ManyToManyRelation[PilotAttribute]
    """PilotAttributes for this pilot. Access through awaitable attributes."""

    class Meta:
        """Tortoise ORM metadata"""

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
