"""
ORM classes for Format data
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..._base import _RaceBase


class RaceFormat(_RaceBase):
    """
    Race formats are profiles of properties used to define parameters of individual races.
    Every race has an assigned format. A race formats may be assigned to a race class,
    which forces RotorHazard to switch to that formatwhen running races within the class.
    """

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    """User-facing name"""
    unlimited_time: Mapped[bool] = mapped_column("race_mode", nullable=False)
    """True if race clock counts up, False if race clock counts down"""
    stage_time_sec: Mapped[int] = mapped_column(nullable=False)
    """The amount of time for staging in seconds"""
    random_stage_delay: Mapped[int] = mapped_column(nullable=False)
    """Maximum amount of random stage delay in milliseconds"""
    race_time_sec: Mapped[int] = mapped_column(nullable=False)
    """Race clock duration in seconds, unused if unlimited_time is True"""
    overtime_sec: Mapped[int] = mapped_column(nullable=False, default=-1)
    """Overtime duration in seconds, -1 for unlimited, unused if unlimited_time is True"""
