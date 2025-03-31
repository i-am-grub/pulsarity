import pytest

from quart.typing import TestClientProtocol

from quart_auth import authenticated_client

from pulsarity.extensions import RHApplication
from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.database import User, Role, Permission


@pytest.mark.asyncio
async def test_webserver_unauthorized(client: TestClientProtocol):
    response = await client.get("/api/pilot/all")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webserver_lack_permissions(app: RHApplication, _setup_database):
    client: TestClientProtocol = app.test_client()

    permissions_: set[Permission] = set()
    permissions = await Permission.all()
    for permission in permissions:
        if permission.value != SystemDefaultPerms.READ_PILOTS:
            permissions_.add(permission)
            break

    role = await Role.create(name="TEST")
    await role.add_permissions(*permissions_)

    roles: set[Role] = set()
    roles.add(role)

    user = await User.create(username="test")
    await user._roles.add(*roles)

    async with authenticated_client(client, user.auth_id.hex):
        response = await client.get("/api/pilot/all")
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_webserver_authorized(
    app: RHApplication, default_user_creds: tuple[str], _setup_database
):
    client: TestClientProtocol = app.test_client()

    user = await User.get_by_username(default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        response = await client.get("/api/pilot/all")
        assert response.status_code == 200
