"""
Test the system database
"""

import pytest

from pulsarity.database.user import User


@pytest.mark.asyncio
async def test_user_create():
    """
    Test adding a user to the database
    """

    username = "foo"

    assert await User.get_or_none(username=username) is None
    user = await User.create(username=username)
    assert await User.get_or_none(username=username) is not None
    assert user.username == username
