"""
Database objects and access
"""

from .permission import Permission, SystemDefaultPerms
from .pilot import Pilot, PilotAttribute
from .raceformat import RaceFormat, RaceSchedule
from .role import Role
from .user import User

__all__ = [
    "User",
    "Role",
    "Permission",
    "Pilot",
    "PilotAttribute",
    "RaceFormat",
    "RaceSchedule",
    "SystemDefaultPerms",
]


async def setup_default_objects():
    """
    Setup the default objects in the system database
    """

    await Permission.verify_persistant()
    await Role.verify_persistant()
    await User.verify_persistant()
