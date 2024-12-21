import pytest

from quart.typing import TestClientProtocol

from quart_auth import authenticated_client

from prophazard.extensions import RHApplication
from prophazard.database.user._enums import SystemDefaults
from prophazard.database.user import User, Role, Permission


@pytest.mark.asyncio
async def test_webserver_unauthorized(client: TestClientProtocol):
    response = await client.get("/pilots")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webserver_lack_permissions(app: RHApplication):
    client: TestClientProtocol = app.test_client()

    database = await app.get_user_database()
    session_maker = database.new_session_maker()

    permissions_: set[Permission] = set()
    async with session_maker() as session:
        permissions = database.permissions.get_all_as_stream(session)
        async for permission in permissions:
            if permission.value != SystemDefaults.READ_PILOTS:
                permissions_.add(permission)
                break

        role = Role("TEST", permissions=permissions_)
        await database.roles.add(session, role)

        roles: set[Role] = set()
        roles.add(role)
        user = User("test", roles=roles)
        await database.users.add(session, user)

    async with authenticated_client(client, user.auth_id.hex):
        response = await client.get("/pilots")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_webserver_authorized(app: RHApplication, default_user_creds: tuple[str]):
    client: TestClientProtocol = app.test_client()

    database = await app.get_user_database()
    user = await database.users.get_by_username(None, default_user_creds[0])
    assert user is not None

    async with authenticated_client(client, user.auth_id.hex):
        response = await client.get("/pilots")
        assert response.status_code == 200
