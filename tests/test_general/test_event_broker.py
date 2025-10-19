"""
Coverage tests for the EventBroker class
"""

import asyncio
import threading

import pytest

from pulsarity.events import EventBroker, EventSetupEvt, RaceSequenceEvt
from pulsarity.utils import background

# pylint: disable=W0212


async def broker_subscriber(broker: EventBroker, check_values: list):
    """
    Event subscriber for tests
    """

    num_values = len(check_values)
    assert num_values != 0

    num_processed = 0
    async for message in broker.subscribe():
        assert message.data == check_values.pop(0)
        num_processed += 1

        if len(check_values) == 0:
            break
    else:
        assert False

    assert num_processed == num_values
    assert len(check_values) == 0


async def broker_publish_test(
    broker: EventBroker,
    event_values: tuple[tuple],
    test_values: list[dict],
    *,
    use_trigger: bool = False,
) -> None:
    """
    Helper setting for up the subscriber and submitting events
    """
    coro = broker_subscriber(broker, test_values)
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)

    for value in event_values:
        if use_trigger:
            await broker.trigger(*value)
        else:
            broker.publish(*value)

    await task


@pytest.mark.asyncio
async def test_single_event_handling():
    """
    Tests publishing a single event to a client
    """
    broker = EventBroker()

    events = [EventSetupEvt.PILOT_ADD]
    values = [{"id": 1}]
    event_values = tuple(zip(events, values))

    await broker_publish_test(broker, event_values, values)


@pytest.mark.asyncio
async def test_multi_event_handling():
    """
    Tests publishing a multiple events to a client with priority
    """
    broker = EventBroker()

    events = [EventSetupEvt.PILOT_ADD] * 3
    values = [{"id": 1}] * 3
    events.append(RaceSequenceEvt.RACE_START)
    values.append({"id": 5})
    event_values = tuple(zip(events, values))

    test_order = [{"id": 5}, {"id": 1}, {"id": 1}, {"id": 1}]

    await broker_publish_test(broker, event_values, test_order)


@pytest.mark.asyncio
async def test_event_async_callback():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    events = [EventSetupEvt.PILOT_ADD]
    values = [{"id": 1}]
    event_values = tuple(zip(events, values))

    flag = asyncio.Event()

    async def test_cb(flag: asyncio.Event, **_):
        flag.set()

    broker.register_event_callback(
        test_cb, EventSetupEvt.PILOT_ADD, default_kwargs={"flag": flag}
    )

    assert not flag.is_set()

    await broker_publish_test(broker, event_values, values, use_trigger=True)

    await background.shutdown(5)

    assert flag.is_set()


@pytest.mark.asyncio
async def disable_test_event_sync_callback():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    events = [EventSetupEvt.PILOT_ADD]
    values = [{"id": 1}]
    event_values = tuple(zip(events, values))

    flag = threading.Event()

    def test_cb(flag: threading.Event, **_):
        flag.set()

    broker.register_event_callback(
        test_cb, EventSetupEvt.PILOT_ADD, default_kwargs={"flag": flag}
    )

    assert not flag.is_set()

    await broker_publish_test(broker, event_values, values, use_trigger=True)

    await background.shutdown(5)

    assert flag.is_set()


@pytest.mark.asyncio
async def test_event_callback_unregister_pass():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    async def test_cb(**_):
        pass

    broker.register_event_callback(test_cb, EventSetupEvt.PILOT_ADD)

    assert len(broker._callbacks[EventSetupEvt.PILOT_ADD.id]) != 0

    broker.unregister_event_callback(test_cb, EventSetupEvt.PILOT_ADD)

    assert len(broker._callbacks[EventSetupEvt.PILOT_ADD.id]) == 0


@pytest.mark.asyncio
async def test_event_callback_unregister_fail():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    async def test_cb(**_):
        pass

    assert len(broker._callbacks[EventSetupEvt.PILOT_ADD.id]) == 0

    with pytest.raises(RuntimeError):
        broker.unregister_event_callback(test_cb, EventSetupEvt.PILOT_ADD)
