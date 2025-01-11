import pytest
from asyncio import Event

from prophazard.extensions import RHApplication
from prophazard.events import EventBroker, EventSetupEvt, RaceSequenceEvt


async def broker_subscriber(event: Event, broker: EventBroker, check_values: list):

    assert len(check_values) != 0

    async for message in broker.subscribe():
        await event.wait()

        assert message[4] == check_values.pop(0)

        if len(check_values) == 0:
            break

    assert len(check_values) == 0


def broker_publisher(event: Event, broker: EventBroker, event_values: tuple[tuple]):
    for value in event_values:
        broker.publish(*value)

    event.set()


@pytest.mark.asyncio
async def test_single_event_handling(app: RHApplication):
    event = Event()
    broker = EventBroker()
    event.clear()

    events = [EventSetupEvt.PILOT_ADD]
    values = [{"id": 1}]

    event_values = tuple(zip(events, values))

    async with app.test_app():
        app.add_background_task(broker_subscriber(event, broker, values))
        broker_publisher(event, broker, event_values)


@pytest.mark.asyncio
async def test_multi_event_handling(app: RHApplication):
    event = Event()
    broker = EventBroker()
    event.clear()

    events = [EventSetupEvt.PILOT_ADD] * 3
    values = [{"id": 1}] * 3

    #
    events.append(RaceSequenceEvt.RACE_START)
    values.append({"id": 5})

    event_values = tuple(zip(events, values))

    # Expect the first value to be grabbed before sorted by priority
    test_order = [{"id": 1}, {"id": 5}, {"id": 1}, {"id": 1}]

    async with app.test_app():
        app.add_background_task(broker_subscriber(event, broker, test_order))
        broker_publisher(event, broker, event_values)
