"""
ORM classes for Format data
"""

import pickle
from dataclasses import dataclass

from tortoise import fields

from pulsarity.database._base import PulsarityBase


@dataclass
class RaceSchedule:
    """
    Settings for scheduling a race
    """

    stage_time_sec: int
    """The amount of time for staging in seconds"""
    random_stage_delay: int
    """Maximum amount of random stage delay in milliseconds"""
    unlimited_time: bool
    """True if race clock counts up, False if race clock counts down"""
    race_time_sec: int
    """Race clock duration in seconds, unused if unlimited_time is True"""
    overtime_sec: int
    """Overtime duration in seconds, -1 for unlimited, unused if unlimited_time is True"""


class RaceFormat(PulsarityBase):
    """
    Race formats are profiles of properties used to define parameters of individual races.
    Every race has an assigned format. A race formats may be assigned to a race class,
    which forces RotorHazard to switch to that formatwhen running races within the class.
    """

    # pylint: disable=R0903

    name = fields.CharField(max_length=80, null=False)
    """User-facing name"""
    _schedule = fields.BinaryField(null=False)
    """Settings for race scheduling"""

    class Meta:
        """Tortoise ORM metadata"""

        app = "event"
        table = "format"

    def __init__(self, name: str, schedule: RaceSchedule):
        """
        Class initialization

        :param schedule: _description_
        """

        super().__init__()
        self.name = name
        self._schedule = pickle.dumps(schedule)

    @property
    def schedule(self) -> RaceSchedule:
        """The race schedule for the race format"""
        return pickle.loads(self._schedule)

    @schedule.setter
    def schedule(self, schedule: RaceSchedule) -> None:
        """Race schedule setter"""
        self._schedule = pickle.dumps(schedule)
