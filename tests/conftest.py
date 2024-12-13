import pytest
import pytest_asyncio

from prophazard import test_client
from prophazard.database.race import RaceDatabaseManager


@pytest_asyncio.fixture()
async def race_database():
    race_database: RaceDatabaseManager = RaceDatabaseManager()
    await race_database.sync_database()
    yield race_database
    await race_database.shutdown()


@pytest_asyncio.fixture()
def client():
    yield test_client()
