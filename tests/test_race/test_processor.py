from collections.abc import Iterable, Sequence

import pytest

from pulsarity.database.raceformat import RaceFormat
from pulsarity.defaults.processors.most_laps import MostLapsProcessor
from pulsarity.interface.timer_manager import ExtendedTimerData
from pulsarity.race.processor import RaceProcessor, RaceProcessorManager, SlotResult


class BadProcessor(RaceProcessor):
    """
    Processor to test bad implementation
    """


class TestProcessor(RaceProcessor):
    """
    Processor to test good implementation
    """

    def __init__(self, race_format: RaceFormat) -> None: ...

    @classmethod
    def get_uid(cls) -> str:
        return "foo"

    def add_lap_record(self, slot: int, record: ExtendedTimerData) -> int: ...

    def remove_lap_record(self, slot: int, key: int) -> None: ...

    def is_slot_done(self, slot_num: int) -> bool: ...

    def get_race_results(self) -> Sequence[SlotResult]: ...

    def get_slot_result(self, slot_num: int) -> SlotResult: ...

    def get_laps(self) -> Iterable[ExtendedTimerData]: ...


def test_register_processor_error():
    """
    Test for registration of a bad interface
    """

    with pytest.raises(TypeError):
        RaceProcessorManager.register(BadProcessor)


def test_register_processor_duplicate_error():
    """
    Test for registration of a bad processor
    """

    RaceProcessorManager.register(TestProcessor)
    with pytest.raises(RuntimeError):
        RaceProcessorManager.register(TestProcessor)


def test_get_processor():
    """
    Test getting a registered processor
    """
    processor = RaceProcessorManager.get_processor("foo")
    assert processor is None

    RaceProcessorManager.register(TestProcessor)
    processor = RaceProcessorManager.get_processor("foo")
    assert processor is not None
    assert processor is TestProcessor


def test_most_laps_processor():
    """
    Test the basics of the most laps processor

    Does not currently test the split lap scoring
    """
    race_format = RaceFormat(race_time_sec=4, overtime_sec=-1)
    processor = MostLapsProcessor(race_format)

    # Test adding 1 lap
    lap1 = ExtendedTimerData(1.0, "foo", 0, 0.0, 0)
    id_ = processor.add_lap_record(0, lap1)
    assert id_ == 0
    assert not processor.is_slot_done(0)

    # Test adding 2 laps (slot not finished)
    lap2 = ExtendedTimerData(3.0, "foo", 0, 0.0, 0)
    id_ = processor.add_lap_record(0, lap2)
    assert id_ == 1
    assert not processor.is_slot_done(0)

    # Test adding 3 laps (slot finished)
    lap3 = ExtendedTimerData(5.0, "foo", 0, 0.0, 0)
    id_ = processor.add_lap_record(0, lap3)
    assert id_ == 2
    assert processor.is_slot_done(0)

    # Test adding second slot (4 laps)
    lap4 = ExtendedTimerData(2.0, "foo", 1, 0.0, 0)
    id_ = processor.add_lap_record(1, lap4)
    assert id_ == 3
    assert not processor.is_slot_done(1)

    # Test adding additional lap for second slot (slot not finished)
    lap5 = ExtendedTimerData(4.0, "foo", 1, 0.0, 0)
    id_ = processor.add_lap_record(1, lap5)
    assert id_ == 4
    assert not processor.is_slot_done(1)

    # Check race results
    results = processor.get_race_results()
    assert results[0].slot_num == 0
    assert results[0].position == 1
    assert results[1].slot_num == 1
    assert results[1].position == 2

    # Add additional lap to change results
    lap6 = ExtendedTimerData(4.5, "foo", 1, 0.0, 0)
    id_ = processor.add_lap_record(1, lap6)
    assert id_ == 5
    assert processor.is_slot_done(1)

    # Verify results changed as expected
    results = processor.get_race_results()
    assert results[0].slot_num == 1
    assert results[0].position == 1
    assert results[1].slot_num == 0
    assert results[1].position == 2

    # Verify total number of laps in processor
    lap_count = 0
    for _ in processor.get_laps():
        lap_count += 1
    assert lap_count == 6

    # Test removing lap
    processor.remove_lap_record(1, 4)
    assert processor.is_slot_done(1)

    # Verify results changed as expected
    results = processor.get_race_results()
    assert results[0].slot_num == 0
    assert results[0].position == 1
    assert results[1].slot_num == 1
    assert results[1].position == 2
