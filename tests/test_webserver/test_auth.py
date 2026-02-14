"""
Test authenticating to the server
"""

import pytest
from httpx import AsyncClient

from pulsarity._protobuf import http_pb2
from pulsarity.database import Permission, Role, SystemDefaultPerms, User


@pytest.mark.asyncio
async def test_webserver_unauthorized(client: AsyncClient):
    """
    Test accessing the ability to access a privileged route without
    being logged in
    """
    response = await client.get("/pilots")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webserver_lack_permissions(client: AsyncClient):
    """
    Test accessing a priviledged route while being logged in,
    but without proper permissions
    """

    permissions_: set[Permission] = set()
    permissions = await Permission.all()
    for permission in permissions:
        if permission.value != SystemDefaultPerms.READ_PILOTS:
            permissions_.add(permission)

    role = await Role.create(name="TEST")
    await role.add_permissions(*permissions_)

    roles: set[Role] = set()
    roles.add(role)

    user = await User.create(username="foo")
    await user.roles.add(*roles)
    await user.update_user_password("bar")

    message = http_pb2.LoginRequest()
    message.username = "foo"
    message.password = "bar"

    header = {"Content-Type": "application/x-protobuf"}
    response = await client.post(
        "/login", content=message.SerializeToString(), headers=header
    )

    assert response.status_code == 200
    assert response.cookies

    response = await client.get("/pilots")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webserver_authorized(authed_client: AsyncClient):
    """
    Test accessing a route while being logged in with proper permissions
    """
    response = await authed_client.get("/pilots")
    assert response.status_code == 200
