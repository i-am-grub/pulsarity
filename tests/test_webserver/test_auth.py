import pytest
from httpx import AsyncClient

from pulsarity.database import Permission, Role, SystemDefaultPerms, User

# pylint: disable=W0212


@pytest.mark.asyncio
async def test_webserver_unauthorized(client: AsyncClient):
    """
    Test accessing the ability to access a privileged route without
    being logged in
    """
    response = await client.get("/api/pilot/all")
    assert response.status_code == 403


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
    await user._roles.add(*roles)
    await user.update_user_password("bar")

    payload = {"username": "foo", "password": "bar"}

    response = await client.post("/login", json=payload)
    assert response.status_code == 200
    assert response.cookies

    response = await client.get("/api/pilot/all")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webserver_authorized(client: AsyncClient, user_creds: tuple[str, ...]):
    """
    Test accessing a route while being logged in with proper permissions
    """
    payload = {"username": user_creds[0], "password": user_creds[1]}

    response = await client.post("/login", json=payload)
    assert response.status_code == 200
    assert response.cookies

    response = await client.get("/api/pilot/all")
    assert response.status_code == 200
