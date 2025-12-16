import asyncio

import pytest_asyncio

from pulsarity import ctx
from pulsarity.utils import background


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def lifespan():
    loop = asyncio.get_running_loop()
    ctx.loop_ctx.set(loop)
    yield
    await background.shutdown(5)
