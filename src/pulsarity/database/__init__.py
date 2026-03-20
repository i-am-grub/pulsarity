"""
Database objects and access
"""

from pulsarity.database.heat import Heat, HeatAttribute
from pulsarity.database.lap import Lap
from pulsarity.database.permission import Permission, SystemDefaultPerms
from pulsarity.database.pilot import Pilot, PilotAttribute
from pulsarity.database.raceclass import RaceClass, RaceClassAttribute
from pulsarity.database.raceevent import RaceEvent, RaceEventAttribute
from pulsarity.database.raceformat import RaceFormat, RulesetField
from pulsarity.database.role import Role
from pulsarity.database.round import Round, RoundAttribute
from pulsarity.database.signal import SignalHistory
from pulsarity.database.slot import Slot, SlotAttribute
from pulsarity.database.user import User

__all__ = [
    "Heat",
    "HeatAttribute",
    "Lap",
    "Permission",
    "Pilot",
    "PilotAttribute",
    "RaceClass",
    "RaceClassAttribute",
    "RaceEvent",
    "RaceEventAttribute",
    "RaceFormat",
    "Role",
    "Round",
    "RoundAttribute",
    "RulesetField",
    "SignalHistory",
    "Slot",
    "SlotAttribute",
    "SystemDefaultPerms",
    "User",
]


async def setup_default_objects():
    """
    Setup the default objects in the system database
    """

    await Permission.verify_persistant()
    await Role.verify_persistant()
    await User.verify_persistant()
