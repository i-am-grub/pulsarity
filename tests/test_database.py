import pytest

from prophazard.database._base._basemanager import _BaseManager
from prophazard.database.race import RaceDatabaseManager, Pilot


@pytest.mark.asyncio
async def test_abc_manager(race_database: RaceDatabaseManager):
    session_maker = race_database.new_session_maker()
    with pytest.raises(TypeError):
        _BaseManager(session_maker)


@pytest.mark.asyncio
async def test_single_default_object(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    pilot_id = await race_database.pilots.add(None, None)
    assert pilot_id == 1

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 1

    pilot = await race_database.pilots.get_by_id(None, pilot_id)
    assert isinstance(pilot, Pilot)


@pytest.mark.asyncio
async def test_single_custom_object(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    pilot_id = await race_database.pilots.add(None, Pilot())
    assert pilot_id == 1

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 1

    pilot = await race_database.pilots.get_by_id(None, pilot_id)
    assert isinstance(pilot, Pilot)


@pytest.mark.asyncio
async def test_multiple_default_objects(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    num_of_objects = 5
    pilot_ids = await race_database.pilots.add_many(None, num_of_objects)
    assert len(pilot_ids) == num_of_objects

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == num_of_objects

    for id in pilot_ids:
        pilot = await race_database.pilots.get_by_id(None, id)
        assert isinstance(pilot, Pilot)


@pytest.mark.asyncio
async def test_multiple_custom_objects(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    num_of_objects = 5
    pilot_ids = await race_database.pilots.add_many(
        None, 0, *[Pilot() for _ in range(num_of_objects)]
    )
    assert len(pilot_ids) == num_of_objects

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == num_of_objects

    for id in pilot_ids:
        pilot = await race_database.pilots.get_by_id(None, id)
        assert isinstance(pilot, Pilot)


@pytest.mark.asyncio
async def test_table_objects(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    num_of_objects = 5
    pilot_ids = await race_database.pilots.add_many(None, num_of_objects)
    assert len(pilot_ids) == num_of_objects

    pilots = await race_database.pilots.get_all(None)
    count = 0
    for pilot in pilots:
        assert isinstance(pilot, Pilot)
        count += 1

    assert count == num_of_objects


@pytest.mark.asyncio
async def test_table_object_stream(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    num_of_objects = 5
    pilot_ids = await race_database.pilots.add_many(None, num_of_objects)
    assert len(pilot_ids) == num_of_objects

    count = 0
    async for pilot in race_database.pilots.get_all_as_stream(None):
        assert isinstance(pilot, Pilot)
        count += 1

    assert count == num_of_objects


@pytest.mark.asyncio
async def test_custom_session(race_database: RaceDatabaseManager):

    session_maker = race_database.new_session_maker()

    async with session_maker() as session:
        num_entries = await race_database.pilots.num_entries(session)
        assert num_entries == 0

        pilot_id = await race_database.pilots.add(session)
        assert pilot_id == 1

        num_entries = await race_database.pilots.num_entries(session)
        assert num_entries == 1

        pilot = await race_database.pilots.get_by_id(session, pilot_id)
        assert isinstance(pilot, Pilot)


@pytest.mark.asyncio
async def test_custom_session_generator(race_database: RaceDatabaseManager):

    session_maker = race_database.new_session_maker()

    async with session_maker() as session:
        num_entries = await race_database.pilots.num_entries(session)
        assert num_entries == 0

        num_of_objects = 5
        pilot_ids = await race_database.pilots.add_many(session, num_of_objects)
        assert len(pilot_ids) == num_of_objects

        count = 0
        async for pilot in race_database.pilots.get_all_as_stream(session):
            assert isinstance(pilot, Pilot)
            count += 1

        assert count == num_of_objects


@pytest.mark.asyncio
async def test_add_duplicate(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    custom_pilot = Pilot(name="name", callsign="callsign")

    pilot1_id = await race_database.pilots.add(None, custom_pilot)
    assert pilot1_id == 1

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 1

    session_maker = race_database.new_session_maker()
    async with session_maker() as session:

        pilot1: Pilot = await race_database.pilots.get_by_id(session, pilot1_id)

        pilot2_id = await race_database.pilots.add_duplicate(session, pilot1)
        assert pilot2_id == 2

        await session.commit()

    pilot1 = await race_database.pilots.get_by_id(None, pilot1_id)
    pilot2: Pilot = await race_database.pilots.get_by_id(None, pilot2_id)

    assert pilot1.id != pilot2.id
    assert pilot1.name == pilot2.name
    assert pilot1.callsign == pilot2.callsign


@pytest.mark.asyncio
async def test_delete_object(race_database: RaceDatabaseManager):

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    new_pilot = Pilot()

    pilot_id = await race_database.pilots.add(None, new_pilot)
    assert pilot_id == 1

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 1

    await race_database.pilots.delete(None, new_pilot)

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0


@pytest.mark.asyncio
async def test_delete_table(race_database: RaceDatabaseManager):
    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0

    num_of_objects = 5
    pilot_ids = await race_database.pilots.add_many(None, num_of_objects)
    assert len(pilot_ids) == num_of_objects

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == num_of_objects

    await race_database.pilots.clear_table(None)

    num_entries = await race_database.pilots.num_entries(None)
    assert num_entries == 0
