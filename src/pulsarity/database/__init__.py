"""
Database objects and access
"""

from pulsarity.database.heat import Heat, HeatAttribute
from pulsarity.database.permission import Permission, SystemDefaultPerms
from pulsarity.database.pilot import Pilot, PilotAttribute
from pulsarity.database.raceclass import RaceClass, RaceClassAttribute
from pulsarity.database.raceevent import RaceEvent, RaceEventAttribute
from pulsarity.database.raceformat import RaceFormat
from pulsarity.database.role import Role
from pulsarity.database.round import Round, RoundAttribute
from pulsarity.database.slot import Slot, SlotAttribute, SlotHistory
from pulsarity.database.user import User

__all__ = [
    "User",
    "Role",
    "Permission",
    "Pilot",
    "PilotAttribute",
    "RaceFormat",
    "SystemDefaultPerms",
    "RaceEvent",
    "RaceEventAttribute",
    "RaceClass",
    "RaceClassAttribute",
    "Round",
    "RoundAttribute",
    "Heat",
    "HeatAttribute",
    "Slot",
    "SlotAttribute",
    "SlotHistory",
]


async def setup_default_objects():
    """
    Setup the default objects in the system database
    """

    await Permission.verify_persistant()
    await Role.verify_persistant()
    await User.verify_persistant()
