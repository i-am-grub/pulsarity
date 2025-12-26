"""
Test the event database
"""

from datetime import timedelta

import pytest
from tortoise.exceptions import IntegrityError

from pulsarity.database import (
    Heat,
    Lap,
    Pilot,
    RaceClass,
    RaceEvent,
    RaceFormat,
    Round,
    Slot,
    SlotHistory,
    SlotHistoryRecord,
)
from pulsarity.interface import TimerMode


@pytest.mark.asyncio
async def test_basic_race_event(basic_event: RaceEvent):
    """
    Test creating and deleting a race event
    """
    assert await RaceEvent.all().count() == 1
    assert basic_event is not None
    assert basic_event.id == 1
    assert await basic_event.raceclasses.all().count() == 0
    assert await basic_event.attributes.all().count() == 0

    await RaceEvent.delete(basic_event)
    assert await RaceEvent.get_by_id(1) is None
    assert await RaceEvent.all().count() == 0


@pytest.mark.asyncio
async def test_basic_raceclass(basic_event: RaceEvent, limited_schedule: RaceFormat):
    """
    Test creating and deleting raceclasses under a parent event
    """
    value = await basic_event.max_raceclass_num
    assert value is None

    async with RaceClass.lock:
        next_num = await basic_event.get_next_raceclass_num()
        raceclass1 = await RaceClass.create(
            name_="Test RaceClass",
            event=basic_event,
            raceclass_num=next_num,
            raceformat=limited_schedule,
        )

    max_num = await basic_event.max_raceclass_num
    assert max_num == 1

    async with RaceClass.lock:
        next_num = await basic_event.get_next_raceclass_num()
        raceclass2 = await RaceClass.create(
            name_="Test RaceClass",
            event=basic_event,
            raceclass_num=next_num,
            raceformat=limited_schedule,
        )

    assert await basic_event.max_raceclass_num == 2
    await raceclass1.delete()
    assert await basic_event.max_raceclass_num == 2
    await raceclass2.delete()
    assert await basic_event.max_raceclass_num is None


@pytest.mark.asyncio
async def test_unique_raceclass(basic_event: RaceEvent, limited_schedule: RaceFormat):
    """
    Test creating a raceclass with non-unique parameters
    """
    value = await basic_event.max_raceclass_num
    assert value is None

    async with RaceClass.lock:
        next_num = await basic_event.get_next_raceclass_num()
        await RaceClass.create(
            name_="Test RaceClass",
            event=basic_event,
            raceclass_num=next_num,
            raceformat=limited_schedule,
        )

    with pytest.raises(IntegrityError):
        await RaceClass.create(
            name_="Test RaceClass",
            event=basic_event,
            raceclass_num=next_num,
            raceformat=limited_schedule,
        )


@pytest.mark.asyncio
async def test_basic_round(basic_raceclass: RaceClass):
    """
    Test creating and deleting rounds under a parent raceclass
    """
    value = await basic_raceclass.max_round_num
    assert value is None

    async with Round.lock:
        next_num = await basic_raceclass.get_next_round_num()
        round1 = await Round.create(raceclass=basic_raceclass, round_num=next_num)

    max_num = await basic_raceclass.max_round_num
    assert max_num == 1

    async with Round.lock:
        next_num = await basic_raceclass.get_next_round_num()
        round2 = await Round.create(raceclass=basic_raceclass, round_num=next_num)

    assert await basic_raceclass.max_round_num == 2
    await round1.delete()
    assert await basic_raceclass.max_round_num == 2
    await round2.delete()
    assert await basic_raceclass.max_round_num is None


@pytest.mark.asyncio
async def test_unique_round(basic_raceclass: RaceClass):
    """
    Test creating a round with non-unique parameters
    """
    value = await basic_raceclass.max_round_num
    assert value is None

    async with Round.lock:
        next_num = await basic_raceclass.get_next_round_num()
        await Round.create(raceclass=basic_raceclass, round_num=next_num)

    with pytest.raises(IntegrityError):
        await Round.create(raceclass=basic_raceclass, round_num=next_num)


@pytest.mark.asyncio
async def test_basic_heat(basic_round: Round):
    """
    Test creating and deleting heats under a parent round
    """
    value = await basic_round.max_heat_num
    assert value is None

    async with Heat.lock:
        next_num = await basic_round.get_next_heat_num()
        Heat1 = await Heat.create(round=basic_round, heat_num=next_num)

    max_num = await basic_round.max_heat_num
    assert max_num == 1

    async with Heat.lock:
        next_num = await basic_round.get_next_heat_num()
        heat2 = await Heat.create(round=basic_round, heat_num=next_num)

    assert await basic_round.max_heat_num == 2
    await Heat1.delete()
    assert await basic_round.max_heat_num == 2
    await heat2.delete()
    assert await basic_round.max_heat_num is None


@pytest.mark.asyncio
async def test_unique_heat(basic_round: Round):
    """
    Test creating a heat with non-unique parameters
    """
    value = await basic_round.max_heat_num
    assert value is None

    async with Heat.lock:
        next_num = await basic_round.get_next_heat_num()
        await Heat.create(round=basic_round, heat_num=next_num)

    with pytest.raises(IntegrityError):
        await Heat.create(round=basic_round, heat_num=next_num)


@pytest.mark.asyncio
async def test_basic_slot(basic_heat: Heat):
    """
    Test creating and deleting slots under a parent heat
    """
    pilot1 = await Pilot.create(callsign="foo")
    pilot2 = await Pilot.create(callsign="bar")

    slot1 = await Slot.create(heat=basic_heat, index=0, pilot=pilot1)
    num_slots = await basic_heat.slots.all().count()
    assert num_slots == 1

    slot2 = await Slot.create(heat=basic_heat, index=1, pilot=pilot2)
    num_slots = await basic_heat.slots.all().count()
    assert num_slots == 2

    await slot1.delete()
    assert await basic_heat.slots.all().count() == 1
    await slot2.delete()
    assert await basic_heat.slots.all().count() == 0


@pytest.mark.asyncio
async def test_unique_slot(basic_heat: Heat):
    """
    Test creating a slot with non-unique parameters
    """
    pilot1 = await Pilot.create(callsign="foo")
    pilot2 = await Pilot.create(callsign="bar")

    await Slot.create(heat=basic_heat, index=0, pilot=pilot1)

    with pytest.raises(IntegrityError):
        await Slot.create(heat=basic_heat, index=0, pilot=pilot2)

    with pytest.raises(IntegrityError):
        await Slot.create(heat=basic_heat, index=1, pilot=pilot1)


@pytest.mark.asyncio
async def test_basic_lap(basic_slot: Slot):
    """
    Test creating and deleting laps under a parent slot
    """
    delta = timedelta(seconds=1)

    lap1 = await Lap.create(slot=basic_slot, time=delta, mode=TimerMode.PRIMARY)
    num_laps = await basic_slot.laps.all().count()
    assert num_laps == 1

    lap2 = await Lap.create(slot=basic_slot, time=delta, mode=TimerMode.SPLIT)
    num_laps = await basic_slot.laps.all().count()
    assert num_laps == 2

    await lap1.delete()
    assert await basic_slot.laps.all().count() == 1
    await lap2.delete()
    assert await basic_slot.laps.all().count() == 0


@pytest.mark.asyncio
async def test_unique_lap(basic_slot: Slot):
    """
    Test creating a lap with non-unique parameters
    """
    delta = timedelta(seconds=1)

    await Lap.create(slot=basic_slot, time=delta, mode=TimerMode.PRIMARY)

    with pytest.raises(IntegrityError):
        await Lap.create(slot=basic_slot, time=delta, mode=TimerMode.PRIMARY)


@pytest.mark.asyncio
async def test_cascade_delete(basic_slot: Slot):
    """
    Test raceclass deletion as a result of event deletion
    """
    slot = await Slot.get_by_id(basic_slot.id)
    assert slot is not None

    delta = timedelta(seconds=1)
    lap = await Lap.create(slot=basic_slot, time=delta, mode=TimerMode.PRIMARY)
    assert await Lap.get_by_id(lap.id) is not None

    heat = await slot.heat
    assert heat is not None

    round_ = await heat.round
    assert round_ is not None

    raceclass = await round_.raceclass
    assert raceclass is not None

    event = await raceclass.event
    assert event is not None

    await event.delete()

    assert await RaceEvent.get_by_id(event.id) is None
    assert await RaceClass.get_by_id(raceclass.id) is None
    assert await Round.get_by_id(round_.id) is None
    assert await Heat.get_by_id(heat.id) is None
    assert await Slot.get_by_id(slot.id) is None
    assert await Lap.get_by_id(lap.id) is None


@pytest.mark.asyncio
async def test_slot_history(basic_slot: Slot):
    """
    Test raceclass deletion as a result of event deletion
    """
    num = 5
    records = [
        SlotHistoryRecord(time=timedelta(0.1 * i), value=i * 0.1) for i in range(num)
    ]
    history = await SlotHistory.create(slot=basic_slot, history=records)

    assert history.id
    assert len(history.history) == num
