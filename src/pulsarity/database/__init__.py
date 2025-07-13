"""
Database objects and access
"""

from pulsarity.database.permission import Permission, SystemDefaultPerms
from pulsarity.database.pilot import Pilot, PilotAttribute
from pulsarity.database.raceformat import RaceFormat, RaceSchedule
from pulsarity.database.role import Role
from pulsarity.database.user import User

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
