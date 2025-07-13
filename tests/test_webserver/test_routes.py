import json

import pytest
from httpx import AsyncClient


async def webserver_login_valid(client: AsyncClient, user_creds: tuple[str]):
    """
    Sends the provided credentials to the login api to check if they are
    valid
    """

    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    data = json.loads(response.json())

    assert data["status"] is True
    reset_required = data["password_reset_required"]
    assert reset_required is not None
    return reset_required


@pytest.mark.asyncio
async def test_webserver_login_valid(client: AsyncClient, user_creds: tuple[str]):
    """
    Test to see if the base credentials are valid through the api
    """
    await webserver_login_valid(client, user_creds)


@pytest.mark.asyncio
async def test_webserver_login_invalid(client: AsyncClient, user_creds: tuple[str]):
    """
    Test to see if the api detects bad credentials
    """
    fake_password = "fake_password"
    login_data = {"username": user_creds[0], "password": fake_password}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    data = json.loads(response.json())

    assert data["status"] is False
    assert "password_reset_required" not in data


@pytest.mark.asyncio
async def test_password_reset_invalid(client: AsyncClient, user_creds: tuple[str]):
    """
    Test reseting a password while providing invalid credentials
    """
    login_data = {"username": user_creds[0], "password": user_creds[1]}
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200

    password = "password"
    assert password != user_creds[1]

    data = {"old_password": password, "new_password": "new_password"}

    response = await client.post("/reset-password", json=data)
    assert response.status_code == 200

    data = json.loads(response.json())
    assert data["status"] is False


@pytest.mark.asyncio
async def test_password_reset_valid(client: AsyncClient, user_creds: tuple[str]):
    """
    Test reseting a password while providing valid credentials
    """
    new_password = "new_password"

    reset_required = await webserver_login_valid(client, user_creds)
    assert reset_required is True

    reset_data = {
        "old_password": user_creds[1],
        "new_password": new_password,
    }

    response = await client.post("/reset-password", json=reset_data)
    assert response.status_code == 200

    data = json.loads(response.json())
    assert data["status"] is True

    new_creds = (user_creds[0], new_password)

    reset_required = await webserver_login_valid(client, new_creds)
    assert reset_required is False
