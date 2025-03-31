"""
Database objects and access
"""

from .user import User
from .role import Role
from .permission import Permission
from .pilot import Pilot, PilotAttribute
from .raceformat import RaceFormat, RaceSchedule

__all__ = [
    "User",
    "Role",
    "Permission",
    "Pilot",
    "PilotAttribute",
    "RaceFormat",
    "RaceSchedule",
]


async def setup_default_objects():
    """
    Setup the default objects in the system database
    """

    await Permission.verify_persistant()
    await Role.verify_persistant()
    await User.verify_persistant()
