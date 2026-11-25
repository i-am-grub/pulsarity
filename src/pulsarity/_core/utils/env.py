"""Application environment."""

import os
import subprocess
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


def uv_in_env() -> bool:
    """Checks if uv is installed in the same env as the current interpreter."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return False
    else:
        return result.returncode == 0


class EnvironmentType(Flag):
    """Enum describing the runtime environment of the application."""

    VENV = auto()
    """Application is running from a venv"""
    GIL = auto()
    """Global interpreter lock is active"""
    RASP_PI = auto()
    """Application is running on a raspberry pi"""
    DOCKER = auto()
    """Application is running in a docker container"""
    PYAPP = auto()
    """Application is deployed with PyApp"""
    UV = auto()
    """uv installed in the same environment as the application"""

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
        if (val := os.getenv("PYAPP")) is not None and int(val):
            env |= cls.PYAPP
        if (val := os.getenv("DOCKER")) is not None and int(val):
            env |= cls.DOCKER
        if uv_in_env():
            env |= cls.UV

        return env
