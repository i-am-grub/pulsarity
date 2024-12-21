import pytest
import pickle

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
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["success"] is True
    assert "reset_required" in data


@pytest.mark.asyncio
async def test_webserver_login_invalid(
    client: TestClientProtocol, default_user_creds: tuple[str]
):

    fake_password = "fake_password"
    login_data = {"username": default_user_creds[0], "password": fake_password}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["success"] is False
    assert "reset_required" not in data


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

        data = {"password": password, "new_password": "new_password"}

        response = await client.post("/reset-password", json=data)
        assert response.status_code == 200

        data = await response.get_json()
        assert data["success"] is False


@pytest.mark.asyncio
async def test_password_reset_valid(app: RHApplication, default_user_creds: tuple[str]):
    client: TestClientProtocol = app.test_client()
    new_password = "new_password"

    database = await app.get_user_database()
    user = await database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    await test_webserver_login_valid(client, default_user_creds)

    async with authenticated_client(client, user.auth_id.hex):

        reset_data = {"password": default_user_creds[1], "new_password": new_password}

        response = await client.post("/reset-password", json=reset_data)
        assert response.status_code == 200

        data = await response.get_json()
        assert data["success"] is True

    new_creds = (default_user_creds[0], new_password)
    await test_webserver_login_valid(client, new_creds)


async def test_pilot_stream(app: RHApplication, default_user_creds: tuple[str]):
    client: TestClientProtocol = app.test_client()

    race_database = await app.get_race_database()
    await race_database.pilots.add_many(None, 1)

    user_database = await app.get_user_database()
    user = await user_database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        async with client.request("/pilots") as connection:

            data = await connection.receive()
            data_ = pickle.loads(data)
            assert data_ is not None
            assert connection.status_code == 200

            await connection.disconnect()
