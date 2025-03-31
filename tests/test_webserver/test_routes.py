import pytest

from quart.typing import TestClientProtocol
from quart_auth import authenticated_client

from pulsarity.extensions import PulsarityApp
from pulsarity.database import User


async def webserver_login_valid(
    client: TestClientProtocol, default_user_creds: tuple[str]
):
    login_data = {"username": default_user_creds[0], "password": default_user_creds[1]}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["status"] is True
    reset_required = data["password_reset_required"]
    assert reset_required is not None
    return reset_required


@pytest.mark.asyncio
async def test_webserver_login_valid(
    app: PulsarityApp, default_user_creds: tuple[str], _setup_database
):
    client = app.test_client()

    async with app.test_app():
        await webserver_login_valid(client, default_user_creds)


@pytest.mark.asyncio
async def test_webserver_login_invalid(
    client: TestClientProtocol, default_user_creds: tuple[str], _setup_database
):

    fake_password = "fake_password"
    login_data = {"username": default_user_creds[0], "password": fake_password}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = await response.get_json()

    assert data["status"] is False
    assert data["password_reset_required"] is None


@pytest.mark.asyncio
async def test_password_reset_invalid(
    app: PulsarityApp, default_user_creds: tuple[str], _setup_database
):
    client: TestClientProtocol = app.test_client()

    user = await User.get_by_username(default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        password = "password"
        assert password != default_user_creds[1]

        data = {"old_password": password, "new_password": "new_password"}

        response = await client.post("/auth/reset-password", json=data)
        assert response.status_code == 200

        data = await response.get_json()
        assert data["status"] is False


@pytest.mark.asyncio
async def test_password_reset_valid(
    app: PulsarityApp, default_user_creds: tuple[str], _setup_database
):
    client: TestClientProtocol = app.test_client()
    new_password = "new_password"

    user = await User.get_by_username(default_user_creds[0])
    assert user is not None

    async with app.test_app():
        reset_required = await webserver_login_valid(client, default_user_creds)
        assert reset_required is True

        async with authenticated_client(client, user.auth_id.hex):

            reset_data = {
                "old_password": default_user_creds[1],
                "new_password": new_password,
            }

            response = await client.post("/auth/reset-password", json=reset_data)
            assert response.status_code == 200

            data = await response.get_json()
            assert data["status"] is True

        new_creds = (default_user_creds[0], new_password)

        reset_required = await webserver_login_valid(client, new_creds)
        assert reset_required is False
