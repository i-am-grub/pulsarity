"""
ORM classes for Format data
"""

from tortoise import fields

from pulsarity.database._base import PulsarityBase


class RaceFormat(PulsarityBase):
    """
    Race formats are profiles of properties used to define parameters of individual races.
    Every race has an assigned format. A race formats may be assigned to a race class,
    which forces RotorHazard to switch to that formatwhen running races within the class.
    """

    # pylint: disable=R0903

    name: fields.Field[str] = fields.CharField(max_length=80, null=False)
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
    processor_id = fields.CharField(max_length=32, nullable=True)
    """The identifer for the format's processor"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "format"

    def __init__(
        self,
        name: str,
        *,
        stage_time_sec: int = 5,
        random_stage_delay: int = 0,
        unlimited_time: bool = False,
        race_time_sec: int = 60,
        overtime_sec: int = 0,
        processor_id: str | None = None,
    ):
        """
        Class initialization

        :param schedule: _description_
        """
        # pylint: disable=R0913

        super().__init__()
        self.name = name
        self.stage_time_sec = stage_time_sec
        self.random_stage_delay = random_stage_delay
        self.unlimited_time = unlimited_time
        self.race_time_sec = race_time_sec
        self.overtime_sec = overtime_sec

        if processor_id is not None:
            self.ruleset_id = processor_id
