import asyncio

from prophazard import prophazard_webserver


def test_application():
    assert asyncio.iscoroutine(prophazard_webserver())
