import json
import pytest

from quart.typing import TestClientProtocol
from quart_auth import authenticated_client

from prophazard.extensions import RHApplication


@pytest.mark.asyncio
async def test_webserver_index(client: TestClientProtocol):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webserver_login_valid(
    client: TestClientProtocol, default_user_creds: tuple[str]
):
    login_data = {"username": default_user_creds[0], "password": default_user_creds[1]}
    response = await client.post("/api/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["status"] is True
    reset_required = data["password_reset_required"]
    assert reset_required is not None
    return reset_required


@pytest.mark.asyncio
async def test_webserver_login_invalid(
    client: TestClientProtocol, default_user_creds: tuple[str]
):

    fake_password = "fake_password"
    login_data = {"username": default_user_creds[0], "password": fake_password}
    response = await client.post("/api/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["status"] is False
    assert data["password_reset_required"] is None


@pytest.mark.asyncio
async def test_password_reset_invalid(
    app: RHApplication, default_user_creds: tuple[str]
):
    client: TestClientProtocol = app.test_client()

    database = await app.get_user_database()
    user = await database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        password = "password"
        assert password != default_user_creds[1]

        data = {"old_password": password, "new_password": "new_password"}

        response = await client.post("/api/reset-password", json=data)
        assert response.status_code == 200

        data = await response.get_json()
        assert data["status"] is False


@pytest.mark.asyncio
async def test_password_reset_valid(app: RHApplication, default_user_creds: tuple[str]):
    client: TestClientProtocol = app.test_client()
    new_password = "new_password"

    database = await app.get_user_database()
    user = await database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    reset_required = await test_webserver_login_valid(client, default_user_creds)
    assert reset_required is True

    async with authenticated_client(client, user.auth_id.hex):

        reset_data = {
            "old_password": default_user_creds[1],
            "new_password": new_password,
        }

        response = await client.post("/api/reset-password", json=reset_data)
        assert response.status_code == 200

        data = await response.get_json()
        assert data["status"] is True

    new_creds = (default_user_creds[0], new_password)
    reset_required = await test_webserver_login_valid(client, new_creds)
    assert reset_required is False


async def test_pilot_stream(app: RHApplication, default_user_creds: tuple[str]):
    client: TestClientProtocol = app.test_client()

    race_database = await app.get_race_database()
    await race_database.pilots.add_many(None, 3)

    user_database = await app.get_user_database()
    user = await user_database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        async with client.request("/api/pilot/all") as connection:

            data = await connection.receive()
            data_ = json.loads(data.decode())
            assert data_ is not None
            assert connection.status_code == 200

            await connection.disconnect()
