from collections.abc import Iterable, Sequence
from itertools import count

import pytest

from pulsarity._core.database.raceformat import RaceFormat
from pulsarity._core.timing_interface.timer_manager import FullLapData
from pulsarity._core.race.ruleset import (
    RaceRuleset,
    RaceRulesetManager,
    RulesetMeta,
    SlotResult,
)
from pulsarity.api.ruleset import LapsManager, RulesetCustomFields


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

    __meta__ = RulesetMeta(uid="foo", fields=RulesetCustomFields)

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

    with pytest.raises(
        TypeError, match="Attempted to register an abstract race ruleset"
    ):
        RaceRulesetManager.register(Badruleset)


def test_register_ruleset_duplicate_error():
    """
    Test for registration of a bad ruleset
    """

    RaceRulesetManager.register(_Testruleset)
    with pytest.raises(
        RuntimeError, match="Interface type with matching identifier already registered"
    ):
        RaceRulesetManager.register(_Testruleset)


def test_get_ruleset():
    """
    Test getting a registered ruleset
    """
    with pytest.raises(KeyError):
        ruleset = RaceRulesetManager.get_ruleset("foo")

    RaceRulesetManager.register(_Testruleset)
    ruleset = RaceRulesetManager.get_ruleset("foo")
    assert ruleset is _Testruleset


def test_all_metrics():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    lap = FullLapData(1000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(2000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4500, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    metrics = manager.get_combined_metrics()
    assert metrics is not None
    assert metrics.total_laps == manager.get_num_laps()
    assert metrics.total_time_ms == manager.get_total_time_ms()
    assert metrics.average_lap_time_ms == manager.get_average_lap_time()
    assert metrics.fastest_time_ms == manager.get_fastest_time()
    consec_metrics = manager.get_fastest_consecutive_metric()
    assert consec_metrics is not None
    assert metrics.fastest_consec_base == consec_metrics.consec_base
    assert metrics.fastest_consec_time_ms == consec_metrics.consec_time_ms


def test_all_metrics_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    lap = FullLapData(1000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(2000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    lap = FullLapData(4000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)

    metrics = manager.get_combined_metrics(True)
    assert metrics is not None
    assert metrics.total_laps == manager.get_num_laps(True)
    assert metrics.total_time_ms == manager.get_total_time_ms(True)
    assert metrics.average_lap_time_ms == manager.get_average_lap_time(True)
    assert metrics.fastest_time_ms == manager.get_fastest_time(True)
    consec_metrics = manager.get_fastest_consecutive_metric(True)
    assert consec_metrics is not None
    assert metrics.fastest_consec_base == consec_metrics.consec_base
    assert metrics.fastest_consec_time_ms == consec_metrics.consec_time_ms


def test_laps_manager_fastest():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    assert manager.get_fastest_time() is None

    lap = FullLapData(1000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1000

    lap = FullLapData(2000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1000

    lap = FullLapData(4000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 1000

    lap = FullLapData(4500, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 500

    lap = FullLapData(6000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time() == 500


def test_laps_manager_fastest_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    assert manager.get_fastest_time(True) is None

    lap = FullLapData(1000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) is None

    lap = FullLapData(2000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 1000

    lap = FullLapData(4000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 1000

    lap = FullLapData(4500, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 500

    lap = FullLapData(6000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    assert manager.get_fastest_time(True) == 500


def test_laps_manager_consecutive():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    num_laps = 0
    total_time = 0
    prev_time = 0
    consec = 3

    assert manager.get_fastest_consecutive_metric(False, consec) is None

    lap = FullLapData(1000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(5000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(7000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(False, consec) == (
        num_laps,
        total_time,
    )

    lap = FullLapData(9000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(False, consec) != (
        num_laps,
        total_time,
    )
    assert manager.get_fastest_consecutive_metric(False, consec) == (consec, 7000)

    lap = FullLapData(11_000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(False, consec) == (consec, 6000)


def test_laps_manager_consecutive_holeshot():
    """
    Tests some of the basic functionality of the laps manager
    """
    keys = count()
    manager = _TestManager()

    num_laps = -1
    total_time = 0
    prev_time = 0
    consec = 3
    start_time = 1000

    assert manager.get_fastest_consecutive_metric(True, consec) is None

    lap = FullLapData(start_time, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(True, consec) is None

    lap = FullLapData(5000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(True, consec) == (
        num_laps,
        total_time - start_time,
    )

    lap = FullLapData(7000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(True, consec) == (
        num_laps,
        total_time - start_time,
    )

    lap = FullLapData(9000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(True, consec) != (
        num_laps,
        total_time,
    )
    assert manager.get_fastest_consecutive_metric(True, consec) == (consec, 8000)

    lap = FullLapData(11_000, 0, "foo", 0)
    manager.add_lap(next(keys), lap)
    num_laps += 1
    total_time += lap.millis - prev_time
    prev_time = lap.millis

    assert manager.get_fastest_consecutive_metric(True, consec) == (consec, 6000)
