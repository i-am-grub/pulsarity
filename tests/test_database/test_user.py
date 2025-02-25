import pytest

from prophazard.database.user import User


@pytest.mark.asyncio
async def test_user_create():
    username = "foo"
    user = await User.create(username=username)

    assert user.id == 1
    assert user.username == username


@pytest.mark.asyncio
async def test_update_login_time():

    pass
