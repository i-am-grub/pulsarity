import pytest
from quart.typing import TestClientProtocol

from quart_auth import Unauthorized


@pytest.mark.asyncio
async def test_webserver_index(client: TestClientProtocol):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webserver_unauthorized(client: TestClientProtocol):
    response = await client.get("/pilots")
    assert response.status_code != 200


@pytest.mark.asyncio
async def test_webserver_login(client: TestClientProtocol):
    login_data = {"username": "admin", "password": "password"}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()
    assert data == {"success": True}
