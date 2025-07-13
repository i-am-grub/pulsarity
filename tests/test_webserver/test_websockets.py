import asyncio
import uuid

import httpx_ws
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_server_websocket_unauth(client: AsyncClient):
    """
    Test accessing a websocket route without being logged in
    """

    with pytest.raises(httpx_ws.WebSocketUpgradeError):
        async with httpx_ws.aconnect_ws("/server", client):
            pass


@pytest.mark.asyncio
async def _test_server_websocket_auth(
    client: AsyncClient,
    user_creds: tuple[str],
):
    """
    Test accessing a websocket route while being logged in
    """

    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    payload = {"id": str(uuid.uuid4()), "event_id": "heartbeat", "data": {"foo": "bar"}}

    async with httpx_ws.aconnect_ws("/server", client) as ws:
        await asyncio.sleep(2)  # wait for permissions to set

        await ws.send_json(payload)

        async with asyncio.timeout(2):
            recieved = await ws.receive_json()

        assert recieved == payload
