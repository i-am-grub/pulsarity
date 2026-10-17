"""
Database objects and access
"""

from pulsarity._core.database.heat import Heat, HeatAttribute
from pulsarity._core.database.lap import Lap
from pulsarity._core.database.permission import Permission, SystemDefaultPerms
from pulsarity._core.database.pilot import Pilot, PilotAttribute
from pulsarity._core.database.raceclass import RaceClass, RaceClassAttribute
from pulsarity._core.database.raceevent import RaceEvent, RaceEventAttribute
from pulsarity._core.database.raceformat import RaceFormat, RulesetField
from pulsarity._core.database.role import Role
from pulsarity._core.database.round import Round, RoundAttribute
from pulsarity._core.database.signal import SignalHistory
from pulsarity._core.database.slot import Slot, SlotAttribute
from pulsarity._core.database.user import User

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
