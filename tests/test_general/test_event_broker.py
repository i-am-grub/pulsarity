"""
Coverage tests for the EventBroker class
"""

import asyncio
from typing import Iterable, TypedDict

import pytest

from pulsarity.events import EventBroker, SystemEvt
from pulsarity.utils import background
from pulsarity.events.server import (
    system_event,
    SystemEventData,
    EvtPriority,
    ServerStartup,
)
from pulsarity.database.permission import SystemDefaultPerms


@system_event
class LowPriorityEvent(SystemEventData):
    event_id = -1
    priority = EvtPriority.LOW
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


@system_event
class HighPriorityEvent(SystemEventData):
    event_id = -2
    priority = EvtPriority.HIGH
    permission = SystemDefaultPerms.EVENT_WEBSOCKET


async def broker_subscriber(broker: EventBroker, test_values: Iterable[int]):
    """
    Event subscriber for tests
    """

    num_values = len(test_values)
    assert num_values != 0

    idx = 0
    async for message in broker.subscribe():
        assert message._id == test_values[idx]
        idx += 1

        if idx == num_values:
            break
    else:
        assert False


async def broker_publish_test(
    broker: EventBroker,
    event_values: Iterable[tuple[type[SystemEventData], int]],
    test_values: Iterable[int],
    *,
    use_trigger: bool = False,
) -> None:
    """
    Helper setting for up the subscriber and submitting events
    """
    coro = broker_subscriber(broker, test_values)
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)

    for cls, id_ in event_values:
        val = cls(_id=id_)
        if use_trigger:
            await broker.trigger(val)
        else:
            broker.publish(val)

    await task


@pytest.mark.asyncio
async def test_single_event_handling():
    """
    Tests publishing a single event to a client
    """
    broker = EventBroker()

    input_order = ((LowPriorityEvent, 1),)
    test_order = (1,)

    await broker_publish_test(broker, input_order, test_order)


@pytest.mark.asyncio
async def test_multi_event_priority():
    """
    Tests publishing a multiple events to a client with
    event priority
    """
    broker = EventBroker()

    evt_order = [LowPriorityEvent] * 3
    id_order = list(range(3, 0, -1))
    evt_order.append(HighPriorityEvent)
    id_order.append(5)
    input_order = zip(evt_order, id_order)

    test_order = [5, *range(1, 4)]

    await broker_publish_test(broker, input_order, test_order)


class CallbackData(TypedDict):
    flag: asyncio.Event


@pytest.mark.asyncio
async def test_event_async_callback():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    input_order = ((ServerStartup, 1),)
    test_order = (1,)

    flag = asyncio.Event()

    async def test_cb(data: CallbackData):

        data["flag"].set()

    broker.register_event_callback(
        test_cb, SystemEvt.STARTUP, default_kwargs={"flag": flag}
    )

    assert not flag.is_set()

    await broker_publish_test(broker, input_order, test_order, use_trigger=True)

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

    broker.register_event_callback(test_cb, SystemEvt.PILOT_ADD)

    assert len(broker._callbacks[SystemEvt.PILOT_ADD.event_id]) != 0

    broker.unregister_event_callback(test_cb, SystemEvt.PILOT_ADD)

    assert len(broker._callbacks[SystemEvt.PILOT_ADD.event_id]) == 0


@pytest.mark.asyncio
async def test_event_callback_unregister_fail():
    """
    Test running callbacks upon a event triggering
    """

    broker = EventBroker()

    async def test_cb(**_):
        pass

    assert len(broker._callbacks[SystemEvt.PILOT_ADD.event_id]) == 0

    with pytest.raises(RuntimeError):
        broker.unregister_event_callback(test_cb, SystemEvt.PILOT_ADD)
