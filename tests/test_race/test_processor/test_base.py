from collections.abc import Iterable, Sequence
from itertools import count

import pytest

from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import FullLapData
from pulsarity.race.ruleset import (
    LapsManager,
    RaceRuleset,
    RacerulesetManager,
    SlotResult,
)


class _TestManager(LapsManager):
    def get_score(self): ...

    def add_lap_cb(self, *_) -> None: ...

    def remove_lap_cb(self, *_) -> None: ...


class Badruleset(RaceRuleset):
    """
    ruleset to test bad implementation
    """


class _Testruleset(RaceRuleset):
    """
    ruleset to test good implementation
    """

    class Meta:
        """ruleset metadata"""

        uid = "foo"
        fields = ()

    def __init__(self, race_format: RaceFormat) -> None: ...

    def add_lap_record(self, slot: int, record: FullLapData) -> int: ...

    def remove_lap_record(self, slot: int, key: int) -> None: ...

    def is_slot_done(self, slot_num: int) -> bool: ...

    def all_slots_finished(self): ...

    def get_race_results(self) -> Sequence[SlotResult]: ...

    def get_slot_result(self, slot_num: int) -> SlotResult: ...

    def get_laps_iterable(self) -> Iterable[FullLapData]: ...


def test_register_ruleset_error():
    """
    Test for registration of a bad interface
    """

    with pytest.raises(TypeError):
        RacerulesetManager.register(Badruleset)


def test_register_ruleset_duplicate_error():
    """
    Test for registration of a bad ruleset
    """

    RacerulesetManager.register(_Testruleset)
    with pytest.raises(RuntimeError):
        RacerulesetManager.register(_Testruleset)


def test_get_ruleset():
    """
    Test getting a registered ruleset
    """
    with pytest.raises(KeyError):
        ruleset = RacerulesetManager.get_ruleset("foo")

    RacerulesetManager.register(_Testruleset)
    ruleset = RacerulesetManager.get_ruleset("foo")
    assert ruleset is _Testruleset


def test_all_metrics():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    lap = FullLapData(1.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(2.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4.5, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    metrics = manager.get_combined_metrics()
    assert metrics.total_laps == manager.get_num_laps()
    assert metrics.total_time == manager.get_total_time()
    assert metrics.average_lap_time == manager.get_average_lap_time()
    assert metrics.fastest_time == manager.get_fastest_time()
    assert (
        metrics.fastest_consec_base
        == manager.get_fastest_consecutive_metric().consec_base
    )
    assert (
        metrics.fastest_consec_time
        == manager.get_fastest_consecutive_metric().consec_time
    )


def test_all_metrics_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    lap = FullLapData(1.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(2.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4.5, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    metrics = manager.get_combined_metrics(True)
    assert metrics.total_laps == manager.get_num_laps(True)
    assert metrics.total_time == manager.get_total_time(True)
    assert metrics.average_lap_time == manager.get_average_lap_time(True)
    assert metrics.fastest_time == manager.get_fastest_time(True)
    assert (
        metrics.fastest_consec_base
        == manager.get_fastest_consecutive_metric(True).consec_base
    )
    assert (
        metrics.fastest_consec_time
        == manager.get_fastest_consecutive_metric(True).consec_time
    )


def test_laps_manager_fastest():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    assert manager.get_fastest_time() is None

    lap = FullLapData(1.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1.0

    lap = FullLapData(2.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1.0

    lap = FullLapData(4.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1.0

    lap = FullLapData(4.5, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 0.5

    lap = FullLapData(6.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 0.5


def test_laps_manager_fastest_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    assert manager.get_fastest_time(True) is None

    lap = FullLapData(1.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) is None

    lap = FullLapData(2.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 1.0

    lap = FullLapData(4.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 1.0

    lap = FullLapData(4.5, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 0.5

    lap = FullLapData(6.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 0.5


def test_laps_manager_consecutive():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    num_laps = 0
    total_time = 0.0
    prev_time = 0.0
    consec = 3

    assert manager.get_fastest_consecutive_metric(consec) is None

    lap = FullLapData(1.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(5.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(7.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(9.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(False, consec) != (
        num_laps,
        total_time,
    )
    assert manager.get_fastest_consecutive_metric(False, consec) == (consec, 7.0)

    lap = FullLapData(11.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(False, consec) == (consec, 6.0)


def test_laps_manager_consecutive_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    num_laps = -1
    total_time = 0.0
    prev_time = 0.0
    consec = 3
    start_time = 1.0

    assert manager.get_fastest_consecutive_metric(True, consec) is None

    lap = FullLapData(start_time, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(True, consec) is None

    lap = FullLapData(5.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(True, consec) == (
        num_laps,
        total_time - start_time,
    )

    lap = FullLapData(7.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(True, consec) == (
        num_laps,
        total_time - start_time,
    )

    lap = FullLapData(9.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(True, consec) != (
        num_laps,
        total_time,
    )
    assert manager.get_fastest_consecutive_metric(True, consec) == (consec, 8.0)

    lap = FullLapData(11.0, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.timedelta - prev_time
    prev_time = lap.timedelta

    assert manager.get_fastest_consecutive_metric(True, consec) == (consec, 6.0)
