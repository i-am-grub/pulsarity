import inspect

from prophazard import prophazard_webserver


def test_application():
    assert inspect.iscoroutine(prophazard_webserver())
