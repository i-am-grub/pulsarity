"""Server event serialization definitions."""

from typing import TYPE_CHECKING, override

from pulsarity._core._protobuf.websocket_pb2 import (
    EventID,
    PilotAddData,
    PilotAlterData,
    PilotDeleteData,
    WebsocketEvent,
)
from pulsarity._core.database.permission import SystemDefaultPerms
from pulsarity._core.events._base import EvtPriority, ServerEventData, server_event

if TYPE_CHECKING:
    from pulsarity._core.user_interface.elements import UIElement


@server_event
class SystemHeartBeat(ServerEventData):
    """Heartbeat echo."""

    event_id = EventID.EVENT_HEARTBEAT
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class SystemPermissionUpdate(ServerEventData):
    """Permission update."""

    event_id = EventID.EVENT_PERMISSIONS_UPDATE
    priority = EvtPriority.HIGH
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class ServerStartup(ServerEventData):
    """System startup event."""

    event_id = EventID.EVENT_STARTUP
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class ServerShutdown(ServerEventData):
    """System shutdown event."""

    event_id = EventID.EVENT_SHUTDOWN
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class ServerRestart(ServerEventData):
    """System restart event."""

    event_id = EventID.EVENT_RESTART
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class UIElementUpdate(ServerEventData):
    """User interface element update event."""

    event_id = EventID.EVENT_UI_UPDATE
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.READ_WEBSOCKET

    ui_element: UIElement

    def serialize_message(self) -> bytes:
        update_data = self.ui_element.to_element_update_message()
        return WebsocketEvent(
            event_id=self.event_id, ui_element_update=update_data
        ).SerializeToString()


@server_event
class RaceSchedule(ServerEventData):
    """Race schedule event."""

    event_id = EventID.EVENT_RACE_SCHEDULE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RaceStage(ServerEventData):
    """Race stage event."""

    event_id = EventID.EVENT_RACE_STAGE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RaceStart(ServerEventData):
    """Race schedule event."""

    event_id = EventID.EVENT_RACE_START
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RaceFinish(ServerEventData):
    """Race stop event."""

    event_id = EventID.EVENT_RACE_FINISH
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RaceStop(ServerEventData):
    """Race stop event."""

    event_id = EventID.EVENT_RACE_STOP
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RacePause(ServerEventData):
    """Race stop event."""

    event_id = EventID.EVENT_RACE_PAUSE
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class RaceResume(ServerEventData):
    """Race stop event."""

    event_id = EventID.EVENT_RACE_RESUME
    priority = EvtPriority.HIGHEST
    permission = SystemDefaultPerms.READ_WEBSOCKET


@server_event
class PilotAdd(ServerEventData):
    """Pilot Add event."""

    event_id = EventID.EVENT_PILOT_ADD
    priority = EvtPriority.MEDIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    def serialize_message(self) -> bytes:
        pilot_data = PilotAddData(pilot_id=self.pilot_id)
        return WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_add=pilot_data,
        ).SerializeToString()


@server_event
class PilotAlter(ServerEventData):
    """Pilot alter event."""

    event_id = EventID.EVENT_PILOT_ALTER
    priority = EvtPriority.MEDIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    def serialize_message(self) -> bytes:
        pilot_data = PilotAlterData(pilot_id=self.pilot_id)
        return WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_alter=pilot_data,
        ).SerializeToString()


@server_event
class PilotDelete(ServerEventData):
    """Pilot delete event."""

    event_id = EventID.EVENT_PILOT_DELETE
    priority = EvtPriority.MEDIUM
    permission = SystemDefaultPerms.READ_PILOTS

    pilot_id: int

    @override
    def serialize_message(self) -> bytes:
        pilot_data = PilotDeleteData(pilot_id=self.pilot_id)
        return WebsocketEvent(
            uuid=self.uuid.bytes,
            event_id=self.event_id,
            pilot_delete=pilot_data,
        ).SerializeToString()
