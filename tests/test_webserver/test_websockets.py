import asyncio
import pytest
import uuid
from quart.testing import WebsocketResponseError
from quart_auth import authenticated_client
from quart.typing import TestClientProtocol

from prophazard.extensions import RHApplication
from prophazard.events.enums import SpecialEvt


@pytest.mark.asyncio
async def test_server_websocket_unauth(app: RHApplication):

    client = app.test_client()

    async with client.websocket("/ws/server") as test_websocket:

        with pytest.raises(WebsocketResponseError):
            await test_websocket.receive_json()


@pytest.mark.asyncio
async def test_server_websocket_auth(
    app: RHApplication, default_user_creds: tuple[str]
):

    client: TestClientProtocol = app.test_client()

    user_database = await app.get_user_database()
    user = await user_database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    payload = {"id": str(uuid.uuid4()), "event_id": "heartbeat", "data": {"foo": "bar"}}

    async with (
        authenticated_client(client, user.auth_id.hex),
        client.websocket("/ws/server") as test_websocket,
    ):
        await asyncio.sleep(2)  # wait for permissions to set

        await test_websocket.send_json(payload)

        async with asyncio.timeout(2):
            recieved = await test_websocket.receive_json()

        assert recieved == payload
