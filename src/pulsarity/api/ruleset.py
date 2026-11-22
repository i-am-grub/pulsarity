"""Custom ruleset building blocks."""

from abc import ABC, abstractmethod
from collections import ChainMap
from typing import TYPE_CHECKING, NamedTuple, Self, override

from pulsarity._core.race import metrics
from pulsarity._core.race.metrics import (
    CombinedMetrics,
    ConsecutiveMetric,
    calculate_average_lap_time_ms,
    calculate_combined_metrics,
    calculate_fastest_consecutive_metric,
    calculate_fastest_time_ms,
    calculate_num_laps,
    calculate_total_time_ms,
)
from pulsarity._core.race.ruleset import (
    RaceRuleset,
    RulesetCustomFields,
    RulesetMeta,
    SafeRaceFormat,
    SlotResult,
    register_ruleset,
)
from pulsarity._core.timing_interface.timer_manager import FullLapData, TimerMode
from pulsarity._core.utils.collections import ValueSortedDict

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from _typeshed import SupportsAllComparisons, SupportsBool


__all__ = (
    "CombinedMetrics",
    "ConsecutiveMetric",
    "LapsManager",
    "RaceRuleset",
    "RulesetCustomFields",
    "RulesetMeta",
    "SafeRaceFormat",
    "SlotResult",
    "SoloResultData",
    "calculate_average_lap_time_ms",
    "calculate_combined_metrics",
    "calculate_fastest_consecutive_metric",
    "calculate_fastest_time_ms",
    "calculate_num_laps",
    "calculate_total_time_ms",
    "register_ruleset",
)


class SoloResultData(NamedTuple):
    """Basic class for representing individual pilot race data."""

    total_laps: int
    total_time_ms: int
    average_lap_time_ms: int
    fastest_time_ms: int
    fastest_consec_base: int
    fastest_consec_time_ms: int


class LapsManager(ABC):
    """Helper abstract class to assist with storing lap data.

    This class automatically sorts lap data based on the `TimerMode` and
    implements convience comparsion methods to enable sorting based on the
    returned value by the `get_score` method (defined by the child inheriting
    from this class).
    """

    def __init__(self) -> None:
        """Class initalization."""
        self._primary_laps: ValueSortedDict[int, FullLapData] = ValueSortedDict()
        self._split_laps: ValueSortedDict[int, FullLapData] = ValueSortedDict()
        self._all_laps: ChainMap[int, FullLapData] = ChainMap(
            self._primary_laps,
            self._split_laps,
        )

    def __len__(self) -> int:
        """The number of **primary** laps registered to the manager.

        This also enables the `__bool__` evaluation.
        """
        return self._primary_laps.__len__()

    def add_lap(self, key: int, lap: FullLapData) -> None:
        """Save a lap into the manager.

        Args:
            key: The key to save the lap with
            lap: The lap data
        """
        if lap.timer_mode is TimerMode.PRIMARY:
            self._primary_laps[key] = lap
        else:
            self._split_laps[key] = lap
        self.add_lap_cb(key, lap)

    def remove_lap(self, key: int) -> None:
        """Removes a saved lap.

        Args:
            key: The lap key

        Raises:
            KeyError: When key not found
        """
        for map_ in self._all_laps.maps:
            try:
                lap = map_.pop(key)
            except KeyError:
                continue
            break
        else:
            msg = "Key not stored in manager"
            raise KeyError(msg)

        self.remove_lap_cb(key, lap)

    def get_all_laps(self) -> Sequence[FullLapData]:
        """Gets all lap data.

        When planning to only iterate over the data,
        consider using `get_all_laps_iterable` for
        computational efficency instead.

        Returns:
            A sequence of lap data
        """
        return tuple(self._all_laps.values())

    def get_all_laps_iterable(self) -> Iterable[FullLapData]:
        """Gets an iterable that provides all lap data.

        Yields:
            The lap data
        """
        yield from self._all_laps.values()

    def get_last_primary_lap(self) -> FullLapData | None:
        """Get the lap data from the last primary lap.

        Returns:
            The lap data
        """
        if self._primary_laps:
            return self._primary_laps.values()[-1]
        return None

    def get_num_laps(self, holeshot: bool = False) -> int:
        """Get number of laps completed.

        Args:
            holeshot: Holeshot active, defaults to False

        Returns:
            _descriThe number of laps completedption_
        """
        return metrics.calculate_num_laps(self._primary_laps.values(), holeshot)

    def get_total_time_ms(self, holeshot: bool = False) -> int:
        """Get the total time.

        Args:
            holeshot: Holeshot active, defaults to False

        Returns:
            The total time
        """
        return metrics.calculate_total_time_ms(self._primary_laps.values(), holeshot)

    def get_average_lap_time(self, holeshot: bool = False) -> int | None:
        """Get the average lap time.

        Args:
            holeshot: Holeshot active, defaults to False

        Returns:
            The average time
        """
        return metrics.calculate_average_lap_time_ms(
            self._primary_laps.values(), holeshot
        )

    def get_fastest_time(self, holeshot: bool = False) -> int | None:
        """Get the fastest lap time.

        Args:
            holeshot: Holeshot active, defaults to False

        Returns:
            The time associated with the fastest lap
        """
        return metrics.calculate_fastest_time_ms(self._primary_laps.values(), holeshot)

    def get_fastest_consecutive_metric(
        self,
        holeshot: bool = False,
        consec_laps: int = 3,
    ) -> metrics.ConsecutiveMetric | None:
        """Get the fastest consecutive lap times.

        Uses `get_combined_metrics` to generate the metrics
        due to most of its logic is allocated to efficiently
        calculate fastest consecutive time.

        Args:
            holeshot: Holeshot active, defaults to False
            consec_laps: The max consecutive laps, defaults to 3

        Returns:
            A tuple of number of laps and the time associated with the laps
        """
        return metrics.calculate_fastest_consecutive_metric(
            self._primary_laps.values(), holeshot, consec_laps
        )

    def get_combined_metrics(
        self,
        holeshot: bool = False,
        consec_laps: int = 3,
    ) -> metrics.CombinedMetrics | None:
        """Generate multiple metrics at once.

        Includes the following:
        - number of laps completed
        - total time
        - average lap time
        - fastest lap time
        - consecutive lap base
        - fastest consecutive lap time

        Args:
            holeshot: Holeshot active, defaults to False
            consec_laps: The max consecutive laps, defaults to 3

        Returns:
            The calculated metrics
        """
        return metrics.calculate_combined_metrics(
            self._primary_laps.values(), holeshot, consec_laps
        )

    @abstractmethod
    def add_lap_cb(self, key: int, lap: FullLapData) -> None:
        """Callback for a lap being added to the manager.

        Args:
            key: The key for the lap
            lap: The added lap
        """

    @abstractmethod
    def remove_lap_cb(self, key: int, lap: FullLapData) -> None:
        """Callback for a lap being removed from the manager.

        Args:
            key: The key for the lap
            lap: The removed lap
        """

    @abstractmethod
    def get_score(self) -> SupportsAllComparisons:
        """Get the score of the manager based on the currently stored lap data.

        It is recommended to return a tuple to allow for scoring
        across multiple parameters in an order of significance
        (See tuple comparsions in Python)
        """

    @override
    def __eq__(self, other: object):
        if isinstance(other, LapsManager):
            return self.get_score() == other.get_score()
        return NotImplemented

    @override
    def __ne__(self, other: object):
        if isinstance(other, LapsManager):
            return self.get_score() != other.get_score()
        return NotImplemented

    def __lt__(self, other: Self) -> SupportsBool:
        """Less than operation."""
        return self.get_score() < other.get_score()

    def __le__(self, other: Self) -> SupportsBool:
        """Less than or equal operation."""
        return self.get_score() <= other.get_score()

    def __gt__(self, other: Self) -> SupportsBool:
        """Greater than operation."""
        return self.get_score() > other.get_score()

    def __ge__(self, other: Self) -> SupportsBool:
        """Greater than or equal operation."""
        return self.get_score() >= other.get_score()

    @override
    def __hash__(self):
        return object.__hash__(self)
