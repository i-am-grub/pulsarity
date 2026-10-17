import asyncio

import pytest_asyncio

from pulsarity._core import ctx
from pulsarity._core.utils import background


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def lifespan():
    loop = asyncio.get_running_loop()
    loop_token = ctx.loop_ctx.set(loop)
    yield
    ctx.loop_ctx.reset(loop_token)
    await background.shutdown(5)
