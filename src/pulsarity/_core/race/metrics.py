"""
Commonly calculated race data metrics
"""

from collections import deque
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pulsarity.timing_interface.timer_manager import FullLapData


def calculate_num_laps(lap_data: Sequence[FullLapData], holeshot: bool = False) -> int:
    """
    Get number of laps completed

    :param lap_data: A sequence of lap data
    :param holeshot: Holeshot active, defaults to False
    :return: The number of laps completed
    """
    num_laps = len(lap_data)

    if holeshot:
        num_laps -= 1

    return max(num_laps, 0)


def calculate_total_time(
    sorted_lap_data: Sequence[FullLapData], holeshot: bool = False
) -> float:
    """
    Get the total time

    :param sorted_lap_data: A sequence of sorted lap data
    :param holeshot: Holeshot active, defaults to False
    :return: The total time
    """
    if sorted_lap_data:
        last_lap = sorted_lap_data[-1]
        last_time = last_lap.timedelta

        if holeshot:
            first_lap = sorted_lap_data[0]
            return last_time - first_lap.timedelta

        return last_time

    return 0.0


def calculate_average_lap_time(
    sorted_lap_data: Sequence[FullLapData], holeshot: bool = False
) -> float | None:
    """
    Get the average lap time

    :param sorted_lap_data: A sequence of sorted lap data
    :param holeshot: Holeshot active, defaults to False
    :return: The average time
    """
    total_time = calculate_total_time(sorted_lap_data, holeshot)
    num_laps = calculate_num_laps(sorted_lap_data, holeshot)

    if total_time and num_laps:
        return total_time / num_laps

    return None


class ConsecutiveMetric(NamedTuple):
    """
    Number of laps and the time associated with consecutive laps
    """

    consec_base: int
    consec_time: float


def calculate_fastest_time(
    sorted_lap_data: Iterable[FullLapData], holeshot: bool = False
) -> float | None:
    """
    Get the fastest lap time

    :param sorted_lap_data: An iterable of sorted lap data
    :param holeshot: Holeshot active, defaults to False
    :return: The time associated with the fastest lap
    """
    fastest_time = float("inf")
    prev_time: float = 0.0
    num_laps: int = 0

    start = 0 if holeshot else 1
    for num_laps, lap in enumerate(sorted_lap_data, start):
        if not num_laps:
            prev_time = lap.timedelta
            continue

        time_diff = lap.timedelta - prev_time
        prev_time = lap.timedelta

        fastest_time = min(fastest_time, time_diff)

    if not num_laps:
        return None

    return fastest_time


def calculate_fastest_consecutive_metric(
    sorted_lap_data: Iterable[FullLapData],
    holeshot: bool = False,
    max_laps: int = 3,
) -> ConsecutiveMetric | None:
    """
    Get the fastest consecutive lap times

    Uses `get_combined_metrics` to generate the metrics
    due to most of its logic is allocated to efficiently
    calculate fastest consecutive time.

    :param sorted_lap_data: An iterable of sorted lap data
    :param holeshot: Holeshot active, defaults to False
    :param max_laps: The max consecutive laps, defaults to 3
    :return: A tuple of number of laps and the time associated with the laps
    """
    metrics = calculate_combined_metrics(sorted_lap_data, holeshot, max_laps)
    if metrics is None:
        return None
    return ConsecutiveMetric(
        metrics.fastest_consec_base,
        metrics.fastest_consec_time,
    )


class CombinedMetrics(NamedTuple):
    """
    A combination of multiple metrics that can be
    calculated together efficiently
    """

    total_laps: int
    total_time: float
    average_lap_time: float
    fastest_time: float
    fastest_consec_base: int
    fastest_consec_time: float


def calculate_combined_metrics(
    sorted_lap_data: Iterable[FullLapData],
    holeshot: bool = False,
    consec_laps: int = 3,
) -> CombinedMetrics | None:
    """
    Generate multiple metrics at once.

    Includes the following:
    - number of laps completed
    - total time
    - average lap time
    - fastest lap time
    - consecutive lap base
    - fastest consecutive lap time

    :param sorted_lap_data: An iterable of sorted lap data
    :param holeshot: Holeshot active, defaults to False
    :param max_laps: The max consecutive laps, defaults to 3
    :return: The generated metrics
    """
    store: deque[float] = deque(maxlen=consec_laps + 1)
    fastest_time = float("inf")
    fastest_consec_time = float("inf")

    prev_time: float = 0.0
    windowed_time: float = 0.0
    num_laps: int = 0
    total_time: float = 0.0

    start = 0 if holeshot else 1
    for num_laps, lap in enumerate(sorted_lap_data, start):
        if not num_laps:
            prev_time = lap.timedelta
            continue

        time_diff = lap.timedelta - prev_time
        store.append(time_diff)
        windowed_time += time_diff
        total_time += time_diff
        prev_time = lap.timedelta

        fastest_time = min(fastest_time, time_diff)

        if len(store) > consec_laps:
            windowed_time -= store.popleft()
            fastest_consec_time = min(fastest_consec_time, windowed_time)
        else:
            fastest_consec_time = windowed_time

    if not num_laps:
        return None

    consec_laps_ = min(consec_laps, num_laps)
    return CombinedMetrics(
        num_laps,
        total_time,
        total_time / num_laps,
        fastest_time,
        consec_laps_,
        fastest_consec_time,
    )
