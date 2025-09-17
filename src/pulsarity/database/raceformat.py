"""
ORM classes for Format data
"""

from tortoise import fields

from pulsarity.database._base import PulsarityBase


class RaceFormat(PulsarityBase):
    """
    The properties that govern how a race is conducted
    """

    # pylint: disable=R0903

    name: fields.Field[str] = fields.CharField(max_length=80)
    """User-facing name"""
    stage_time_sec = fields.IntField(default=3)
    """The amount of time for staging in seconds"""
    random_stage_delay = fields.IntField(default=2)
    """Maximum amount of random stage delay in milliseconds"""
    unlimited_time = fields.BooleanField(default=False)
    """True if race clock counts up, False if race clock counts down"""
    race_time_sec = fields.IntField(default=60)
    """Race clock duration in seconds, unused if unlimited_time is True"""
    overtime_sec = fields.IntField(default=0)
    """Overtime duration in seconds, -1 for unlimited, unused if unlimited_time is True"""
    processor_id = fields.CharField(max_length=32)
    """The identifer for the format's processor"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "format"
