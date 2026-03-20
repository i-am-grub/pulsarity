from pulsarity.defaults.rulesets.most_laps import MostLapsruleset
from pulsarity.interface.timer_manager import FullLapData
from pulsarity.race.ruleset import SafeRaceFormat


def test_most_laps_ruleset():
    """
    Test the basics of the most laps ruleset

    Does not currently test the split lap scoring
    """
    race_time_sec = 4
    overtime_sec = -1
    fields = {field.name: field.default for field in MostLapsruleset.Meta.fields}

    race_format = SafeRaceFormat(0, 0, False, race_time_sec, overtime_sec, fields)
    ruleset = MostLapsruleset(race_format)

    # Test adding 1 lap
    lap1 = FullLapData(1.0, 0, "foo", 0)
    id_ = ruleset.add_lap_record(0, lap1)
    assert id_ == 0
    assert not ruleset.is_slot_done(0)

    # Test adding 2 laps (slot not finished)
    lap2 = FullLapData(3.0, 0, "foo", 0)
    id_ = ruleset.add_lap_record(0, lap2)
    assert id_ == 1
    assert not ruleset.is_slot_done(0)

    # Test adding 3 laps (slot finished)
    lap3 = FullLapData(5.0, 0, "foo", 0)
    id_ = ruleset.add_lap_record(0, lap3)
    assert id_ == 2
    assert ruleset.is_slot_done(0)

    # Test adding second slot (4 laps)
    lap4 = FullLapData(2.0, 1, "foo", 0)
    id_ = ruleset.add_lap_record(1, lap4)
    assert id_ == 3
    assert not ruleset.is_slot_done(1)

    # Test adding additional lap for second slot (slot not finished)
    lap5 = FullLapData(4.0, 1, "foo", 0)
    id_ = ruleset.add_lap_record(1, lap5)
    assert id_ == 4
    assert not ruleset.is_slot_done(1)

    # Check race results
    results = ruleset.get_race_results()
    assert results[0].slots[0] == 0
    assert results[0].position == 1
    assert results[1].slots[0] == 1
    assert results[1].position == 2

    # Add additional lap to change results
    lap6 = FullLapData(4.5, 1, "foo", 0)
    id_ = ruleset.add_lap_record(1, lap6)
    assert id_ == 5
    assert ruleset.is_slot_done(1)

    # Verify results changed as expected
    results = ruleset.get_race_results()
    assert results[0].slots[0] == 1
    assert results[0].position == 1
    assert results[1].slots[0] == 0
    assert results[1].position == 2

    # Verify total number of laps in ruleset
    lap_count = 0
    for _ in ruleset.get_laps_iterable():
        lap_count += 1
    assert lap_count == 6

    # Test removing lap
    ruleset.remove_lap_record(1, 4)
    assert ruleset.is_slot_done(1)

    # Verify total number of laps in ruleset
    lap_count = 0
    for _ in ruleset.get_laps_iterable():
        lap_count += 1
    assert lap_count == 5

    # Verify results changed as expected
    results = ruleset.get_race_results()
    assert results[0].slots[0] == 0
    assert results[0].position == 1
    assert results[1].slots[0] == 1
    assert results[1].position == 2

    # Test adding lap out of timed order (last lap was at 4.5)
    lap7 = FullLapData(1.0, 1, "foo", 0)
    id_ = ruleset.add_lap_record(1, lap7)
    assert id_ == 6

    # Verify slot is still done
    assert ruleset.is_slot_done(1)

    # Verify results changed as expected
    results = ruleset.get_race_results()
    assert results[0].slots[0] == 1
    assert results[0].position == 1
    assert results[1].slots[0] == 0
    assert results[1].position == 2
