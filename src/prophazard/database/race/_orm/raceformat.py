"""
ORM classes for Format data
"""

from dataclasses import dataclass

from sqlalchemy import String, PickleType
from sqlalchemy.orm import Mapped, mapped_column

from ..._base import _RaceBase


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


class RaceFormat(_RaceBase):
    """
    Race formats are profiles of properties used to define parameters of individual races.
    Every race has an assigned format. A race formats may be assigned to a race class,
    which forces RotorHazard to switch to that formatwhen running races within the class.
    """

    # pylint: disable=R0903

    __tablename__ = "format"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    """User-facing name"""
    schedule: Mapped[RaceSchedule] = mapped_column(PickleType, nullable=False)
    """Settings for race scheduling"""

    def __init__(self, schedule: RaceSchedule):
        self.schedule = schedule
