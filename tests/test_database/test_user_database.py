import pytest

from prophazard.database.user import UserDatabaseManager


@pytest.mark.asyncio
async def test_update_password(
    user_database: UserDatabaseManager, default_user_creds: tuple[str]
):

    user = await user_database.users.get_by_username(None, default_user_creds[0])
    password_hash = user._password_hash

    await user_database.users.update_user_password(None, user, "new_password")

    user2 = await user_database.users.get_by_username(None, default_user_creds[0])

    assert user.id == user2.id
    assert user.auth_id == user2.auth_id
    assert password_hash != user2._password_hash


@pytest.mark.asyncio
async def test_update_login_time(
    user_database: UserDatabaseManager, default_user_creds: tuple[str]
):

    user = await user_database.users.get_by_username(None, default_user_creds[0])
    assert user.last_login is None

    await user_database.users.update_user_login_time(None, user)

    user2 = await user_database.users.get_by_username(None, default_user_creds[0])

    assert user.id == user2.id
    assert user.auth_id == user2.auth_id
    assert user2.last_login is not None
