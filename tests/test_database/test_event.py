import pytest
import pytest_asyncio

from pulsarity.database import Heat, RaceClass, RaceEvent, RaceFormat, Round


@pytest_asyncio.fixture(name="limited_schedule")
async def _limited_schedule():
    return await RaceFormat.create(
        name="limited_schedule",
        stage_time_sec=3,
        random_stage_delay=0,
        unlimited_time=False,
        race_time_sec=5,
        overtime_sec=2,
        processor_id="foo-bar",
    )


@pytest_asyncio.fixture(name="basic_event")
async def _basic_event():
    return await RaceEvent.create(name="Test Event")


@pytest_asyncio.fixture(name="basic_raceclass")
async def _basic_raceclass(basic_event: RaceEvent, limited_schedule: RaceFormat):
    async with RaceClass.lock:
        value = await basic_event.get_next_raceclass_num()
        return await RaceClass.create(
            name="Test RaceClass",
            event=basic_event,
            raceclass_num=value,
            raceformat=limited_schedule,
        )


@pytest_asyncio.fixture(name="basic_round")
async def _basic_round(basic_raceclass: RaceClass):
    async with Round.lock:
        value = await basic_raceclass.get_next_round_num()
        return await Round.create(raceclass=basic_raceclass, round_num=value)


@pytest_asyncio.fixture(name="basic_heat")
async def _basic_heat(basic_round: Round):
    async with Heat.lock:
        value = await basic_round.get_next_heat_num()
        return await Heat.create(round=basic_round, heat_num=value)


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
            name="Test RaceClass",
            event=basic_event,
            raceclass_num=next_num,
            raceformat=limited_schedule,
        )

    max_num = await basic_event.max_raceclass_num
    assert max_num == 1

    async with RaceClass.lock:
        next_num = await basic_event.get_next_raceclass_num()
        raceclass2 = await RaceClass.create(
            name="Test RaceClass",
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
async def test_basic_heat(basic_round: Round):
    """
    Test creating and deleting rounds under a parent raceclass
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
async def test_cascade_delete(basic_heat: Heat):
    """
    Test raceclass deletion as a result of event deletion
    """
    heat = await Heat.get_by_id(basic_heat.id)
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
