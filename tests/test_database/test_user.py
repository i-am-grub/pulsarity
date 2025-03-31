import pytest

from pulsarity.database.user import User


@pytest.mark.asyncio
async def test_user_create(_setup_database):
    username = "foo"

    assert await User.get_or_none(username=username) is None
    user = await User.create(username=username)
    assert await User.get_or_none(username=username) is not None
    assert user.username == username


@pytest.mark.asyncio
async def test_update_login_time():

    pass
