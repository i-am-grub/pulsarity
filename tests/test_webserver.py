import pytest
from quart.typing import TestClientProtocol


@pytest.mark.asyncio
async def test_webserver_none(client: TestClientProtocol):
    response = await client.get("/fake")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_webserver_hello(client: TestClientProtocol):
    response = await client.get("/hello")
    assert response.status_code == 200
    assert await response.get_json() == {"hello": 0}


@pytest.mark.asyncio
async def test_webserver_echo(client: TestClientProtocol):
    data = {"name": "foo"}
    response = await client.post("/echo", json=data)
    assert response.status_code == 200
    returned_data = await response.get_json()
    assert returned_data == {"input": data, "extra": True}
