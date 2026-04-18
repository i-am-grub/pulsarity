"""
Enums for system events
"""

from dataclasses import dataclass
from enum import Enum, unique

from pulsarity._protobuf import websocket_pb2
from pulsarity.events import server


@dataclass(frozen=True)
class _EvtData:
    """
    The dataclass used to define event enums
    """

    event_id: websocket_pb2.EventID
    """Identifier for the event. This field should match the protocol buffer value"""


@unique
class SystemEvt(_EvtData, Enum):
    """
    System events
    """

    # Special Events
    PERMISSIONS_UPDATE = websocket_pb2.EVENT_PERMISSIONS_UPDATE
    """User permission update event"""
    STARTUP = server.ServerStartup.event_id
    """System startup event"""
    SHUTDOWN = server.ServerShutdown.event_id
    """System shutdown event"""
    RESTART = server.ServerRestart.event_id
    """System restart event"""

    # Events associated with modification to race objects
    PILOT_ADD = server.PilotAdd.event_id
    """Pilot add event"""
    PILOT_ALTER = server.PilotAlter.event_id
    """Pilot alter event"""
    PILOT_DELETE = server.PilotDelete.event_id
    """Pilot delete event"""

    # Events associated with live race sequence
    RACE_SCHEDULE = server.RaceSchedule.event_id
    """Race scheduled event"""
    RACE_STAGE = server.RaceStage.event_id
    """Race stage event"""
    RACE_START = server.RaceStart.event_id
    """Race start event"""
    RACE_FINISH = server.RaceFinish.event_id
    """Race finish event"""
    RACE_STOP = server.RaceStop.event_id
    """Race stop event"""
    RACE_PAUSE = server.RacePause.event_id
    """Race pause event"""
    RACE_RESUME = server.RaceResume.event_id
    """Race resume event"""
