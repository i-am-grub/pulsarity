from collections.abc import Iterable, Sequence

from pulsarity.database.raceformat import RaceFormat
from pulsarity.interface.timer_manager import FullLapData
from pulsarity.race.processor import RaceProcessor, SlotResult


class MostLapsProcessor(RaceProcessor):
    """
    Processor to test good implementation
    """

    def __init__(self, race_format: RaceFormat) -> None: ...

    @classmethod
    def get_uid(cls) -> str:
        return "foo"

    def add_lap_record(self, slot: int, record: FullLapData) -> int: ...

    def remove_lap_record(self, slot: int, key: int) -> None: ...

    def is_slot_done(self, slot_num: int) -> bool: ...

    def get_race_results(self) -> Sequence[SlotResult]: ...

    def get_slot_results(self, slot_num: int) -> SlotResult: ...

    def get_laps(self) -> Iterable[FullLapData]: ...
