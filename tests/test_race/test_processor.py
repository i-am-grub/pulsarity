from collections.abc import Iterable, Sequence

import pytest

from pulsarity.database.raceformat import RaceFormat
from pulsarity.defaults.processors.most_laps import MostLapsProcessor
from pulsarity.interface.timer_manager import ExtendedTimerData, TimerMode
from pulsarity.race.processor import RaceProcessor, RaceProcessorManager, SlotResult


@pytest.fixture(name="processor_manager")
def _processor_manager():
    yield RaceProcessorManager()


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


def test_register_processor_error(processor_manager: RaceProcessorManager):
    """
    Test for registration of a bad interface
    """

    with pytest.raises(TypeError):
        processor_manager.register(BadProcessor)


def test_register_processor_duplicate_error(processor_manager: RaceProcessorManager):
    """
    Test for registration of a bad processor
    """

    processor_manager.register(TestProcessor)
    with pytest.raises(RuntimeError):
        processor_manager.register(TestProcessor)


def test_get_processor(processor_manager: RaceProcessorManager):
    """
    Test getting a registered processor
    """
    processor = processor_manager.get_processor("foo")
    assert processor is None

    processor_manager.register(TestProcessor)
    processor = processor_manager.get_processor("foo")
    assert processor is not None
    assert processor is TestProcessor


def test_most_laps_processor():
    """
    Test the basics of the most laps processor

    Does not currently test the split lap scoring
    """
    race_format = RaceFormat(race_time_sec=4)
    processor = MostLapsProcessor(race_format)
    lap1 = ExtendedTimerData(1.0, "foo", 0, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(0, lap1)
    assert id_ == 0
    assert not processor.is_slot_done(0)

    lap2 = ExtendedTimerData(3.0, "foo", 0, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(0, lap2)
    assert id_ == 1
    assert not processor.is_slot_done(0)

    lap3 = ExtendedTimerData(5.0, "foo", 0, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(0, lap3)
    assert id_ == 2
    assert processor.is_slot_done(0)

    lap4 = ExtendedTimerData(2.0, "foo", 1, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(1, lap4)
    assert id_ == 3
    assert not processor.is_slot_done(1)

    lap5 = ExtendedTimerData(4.0, "foo", 1, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(1, lap5)
    assert id_ == 4
    assert not processor.is_slot_done(1)

    results = processor.get_race_results()
    assert results[0].slot_num == 0
    assert results[1].slot_num == 1

    lap6 = ExtendedTimerData(4.5, "foo", 1, 0.0, TimerMode.PRIMARY, 0)
    id_ = processor.add_lap_record(1, lap6)
    assert id_ == 5
    assert processor.is_slot_done(1)

    results = processor.get_race_results()
    assert results[0].slot_num == 1
    assert results[1].slot_num == 0

    lap_count = 0
    for _ in processor.get_laps():
        lap_count += 1
    assert lap_count == 6

    processor.remove_lap_record(1, 4)
    assert processor.is_slot_done(1)

    results = processor.get_race_results()
    assert results[0].slot_num == 0
    assert results[1].slot_num == 1
