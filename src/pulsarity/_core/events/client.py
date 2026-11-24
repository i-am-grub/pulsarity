"""Client event handler definitions."""

from uuid import UUID

from pulsarity._core import ctx
from pulsarity._core._protobuf.websocket_pb2 import EventID
from pulsarity._core.database.permission import SystemDefaultPerms
from pulsarity._core.events._base import ClientEventData, client_event
from pulsarity._core.events.server import SystemHeartBeat


@client_event
class ClientHeartbeat(ClientEventData):
    """Client heartbeat."""

    event_id = EventID.EVENT_HEARTBEAT
    permission = SystemDefaultPerms.WRITE_WEBSOCKET

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def process(self):
        websocket = ctx.websocket_ctx.get()
        response = SystemHeartBeat(uuid=self.uuid).message_dump_protobuf()
        await websocket.send_bytes(response)


@client_event
class ClientServerShutdown(ClientEventData):
    """Client commanded system shutdown."""

    event_id = EventID.EVENT_SHUTDOWN
    permission = SystemDefaultPerms.SYSTEM_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def process(self):
        ctx.shutdown_app.set()


@client_event
class ClientServerRestart(ClientEventData):
    """Client commanded system restart."""

    event_id = EventID.EVENT_RESTART
    permission = SystemDefaultPerms.SYSTEM_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def process(self):
        ctx.restart_app = True
        ctx.shutdown_app.set()


@client_event
class ClientScheduleRace(ClientEventData):
    """Client commanded race schedule."""

    event_id = EventID.EVENT_RACE_SCHEDULE
    permission = SystemDefaultPerms.RACE_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def process(self):
        raise NotImplementedError


@client_event
class ClientStopRace(ClientEventData):
    """Client commanded race stop."""

    event_id = EventID.EVENT_RACE_STOP
    permission = SystemDefaultPerms.RACE_CONTROL

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid)

    async def process(self):
        ctx.race_manager.stop_race()


@client_event
class ClientPilotAdd(ClientEventData):
    """Client commanded pilot add."""

    event_id = EventID.EVENT_PILOT_ADD
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_add.pilot_id)

    async def process(self):
        raise NotImplementedError


@client_event
class ClientPilotAlter(ClientEventData):
    """Client commanded pilot alter."""

    event_id = EventID.EVENT_PILOT_ALTER
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_alter.pilot_id)

    async def process(self):
        raise NotImplementedError


@client_event
class ClientPilotDelete(ClientEventData):
    """Client commanded pilot delete event."""

    event_id = EventID.EVENT_PILOT_DELETE
    permission = SystemDefaultPerms.WRITE_PILOTS

    pilot_id: int

    @classmethod
    def from_ws_event(cls, msg):
        uuid = UUID(bytes=msg.uuid)
        return cls(uuid, msg.pilot_delete.pilot_id)

    async def process(self):
        raise NotImplementedError
