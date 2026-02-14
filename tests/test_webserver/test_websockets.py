"""
Test websocket access
"""

import asyncio
import uuid

import httpx_ws
import pytest
from httpx import AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport

from pulsarity._protobuf import http_pb2, websocket_pb2
from pulsarity.webserver import app


@pytest.mark.asyncio
async def test_server_websocket_unauth():
    """
    Test accessing a websocket route without being logged in
    """
    transport = ASGIWebSocketTransport(app=app.generate_api_application())
    async with AsyncClient(transport=transport, base_url="https://localhost") as client:
        with pytest.raises(httpx_ws.WebSocketDisconnect):
            async with httpx_ws.aconnect_ws("/ws", client):
                ...


@pytest.mark.asyncio
async def test_server_websocket_auth(user_creds: tuple[str, str]):
    """
    Test accessing a websocket route while being logged in
    """
    evt = websocket_pb2.WebsocketEvent()
    evt.uuid = uuid.uuid4().bytes
    evt.event_id = websocket_pb2.EVENT_HEARTBEAT

    transport = ASGIWebSocketTransport(app=app.generate_api_application())
    async with AsyncClient(transport=transport, base_url="https://localhost") as client:
        message = http_pb2.LoginRequest()
        message.username = user_creds[0]
        message.password = user_creds[1]

        header = {"Content-Type": "application/x-protobuf"}
        response = await client.post(
            "/login", content=message.SerializeToString(), headers=header
        )

        assert response.status_code == 200

        async with httpx_ws.aconnect_ws("/ws", client) as ws:  # type: ignore
            await ws.send_bytes(evt.SerializeToString())

            async with asyncio.timeout(5.0):
                # Simulate reading JSON as the client
                data = await ws.receive_bytes()
                recieved = websocket_pb2.WebsocketEvent.FromString(data)

            assert recieved.uuid == evt.uuid
