import asyncio
import uuid

import httpx_ws
import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport

from pulsarity.webserver import generate_application


@pytest_asyncio.fixture(name="websocket_client")
async def authenticated_websocket_client(user_creds: tuple[str]):
    """
    Generates a client capable of using websockets
    """

    transport = ASGIWebSocketTransport(app=generate_application(test_mode=True))
    async with AsyncClient(
        transport=transport, base_url="https://localhost"
    ) as client_:
        login_data = {"username": user_creds[0], "password": user_creds[1]}
        response = await client_.post("/login", json=login_data)
        assert response.status_code == 200

        # https://github.com/frankie567/httpx-ws/discussions/79#discussioncomment-12205278
        try:
            yield client_
            transport.exit_stack = None
        finally:
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_server_websocket_unauth(client: AsyncClient):
    """
    Test accessing a websocket route without being logged in
    """

    with pytest.raises(httpx_ws.WebSocketUpgradeError):
        async with httpx_ws.aconnect_ws("/server", client):
            pass


@pytest.mark.asyncio
async def test_server_websocket_auth(websocket_client: AsyncClient):
    """
    Test accessing a websocket route while being logged in
    """

    payload = {"id": str(uuid.uuid4()), "event_id": "heartbeat", "data": {"foo": "bar"}}

    async with httpx_ws.aconnect_ws("/server", websocket_client) as ws:
        await asyncio.sleep(0.5)  # wait for permissions to set

        await ws.send_json(payload)

        async with asyncio.timeout(2):
            recieved = await ws.receive_json()

        assert recieved == payload
