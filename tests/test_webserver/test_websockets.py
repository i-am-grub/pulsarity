import asyncio
import uuid

import httpx_ws
import pytest
from httpx import AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport

from pulsarity.webserver import generate_application


@pytest.mark.asyncio
async def test_server_websocket_unauth():
    """
    Test accessing a websocket route without being logged in
    """
    transport = ASGIWebSocketTransport(app=generate_application(test_mode=True))
    async with AsyncClient(transport=transport, base_url="https://localhost") as client:
        with pytest.raises(httpx_ws.WebSocketDisconnect):
            async with httpx_ws.aconnect_ws("/server", client):
                ...


@pytest.mark.asyncio
async def test_server_websocket_auth(user_creds: tuple[str, str]):
    """
    Test accessing a websocket route while being logged in
    """
    login_data = {"username": user_creds[0], "password": user_creds[1]}
    payload = {"id": str(uuid.uuid4()), "event_id": "heartbeat", "data": {"foo": "bar"}}

    transport = ASGIWebSocketTransport(app=generate_application(test_mode=True))
    async with AsyncClient(transport=transport, base_url="https://localhost") as client:
        response = await client.post("/login", json=login_data)
        assert response.status_code == 200

        async with httpx_ws.aconnect_ws("/server", client) as ws:
            await ws.send_json(payload)

            async with asyncio.timeout(2):
                recieved = await ws.receive_json()

            assert recieved == payload
