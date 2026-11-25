"""Application environment."""

import os
import sys
from enum import Flag, auto
from pathlib import Path


def is_raspberry_pi() -> bool:
    """Check for chipsets that are (nearly) raspberry pi exclusive."""
    try:
        with Path("/proc/cpuinfo").open() as cpuinfo:
            for line in cpuinfo:
                if line.startswith("Hardware"):
                    _, value = line.strip().split(":", 1)
                    if value.strip() in (
                        "BCM2708",
                        "BCM2709",
                        "BCM2711",
                        "BCM2835",
                        "BCM2836",
                    ):
                        return True
    except OSError:
        return False
    return False


class EnvironmentType(Flag):
    """Enum describing the runtime environment of the application."""

    VENV = auto()
    """Application is running from a venv"""
    GIL = auto()
    """Global interpreter lock is active"""
    RASP_PI = auto()
    """"""
    DOCKER = auto()
    """Application is running in a docker container"""
    PYAPP = auto()
    """Application is deployed with PyApp"""

    @classmethod
    def get_env_type(cls) -> EnvironmentType:
        """Get the type of environment the application is currently running in.

        Returns:
            The environment type enum
        """
        env = EnvironmentType(0)
        if sys.prefix != sys.base_prefix:
            env |= cls.VENV
        if sys._is_gil_enabled():
            env |= cls.GIL
        if is_raspberry_pi():
            env |= cls.RASP_PI
        if os.getenv("PYAPP"):
            env |= cls.PYAPP
        if os.getenv("DOCKER"):
            env |= cls.DOCKER

        return env
