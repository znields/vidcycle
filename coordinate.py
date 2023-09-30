from datetime import datetime, timedelta
import json
from typing import Optional, List
import geopy.distance
import functools


class Coordinate:
    def __init__(
        self,
        timestamp: datetime,
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=4, default=str)

    @staticmethod
    def weighted_average(
        a: "Coordinate", b: "Coordinate", a_weight: float
    ) -> "Coordinate":
        assert 0.0 <= a_weight <= 1.0
        b_weight = 1.0 - a_weight

        return Coordinate(
            timestamp=datetime.fromtimestamp(
                (a.timestamp.timestamp() * a_weight)
                + (b.timestamp.timestamp() * b_weight)
            ),
            latitude=(a.latitude * a_weight) + (b.latitude * b_weight),
            longitude=(a.longitude * a_weight) + (b.longitude * b_weight),
        )

    @staticmethod
    def distance(a: "Coordinate", b: "Coordinate") -> "Coordinate":
        return geopy.distance.geodesic(
            (a.latitude, a.longitude), (b.latitude, b.longitude)
        ).km


class Segment:
    def __init__(self, coordinates: List[Coordinate]) -> None:
        reversed_coordinates = []
        for coordinate in coordinates[::-1]:
            if (
                coordinate.latitude is not None
                and coordinate.longitude is not None
                and (
                    len(reversed_coordinates) == 0
                    or Coordinate.distance(coordinate, reversed_coordinates[-1]) < 1
                )
            ):
                reversed_coordinates.append(coordinate)
        self.coordinates = reversed_coordinates[::-1]

    @functools.lru_cache(maxsize=None)
    def get_coordinate(self, time: datetime) -> Optional[Coordinate]:
        for a, b in zip(self.coordinates[:-1], self.coordinates[1:]):
            if a.timestamp <= time <= b.timestamp:
                a_timestamp = a.timestamp.timestamp()
                b_timestamp = b.timestamp.timestamp()
                a_weight = (b_timestamp - time.timestamp()) / (
                    b_timestamp - a_timestamp
                )
                return Coordinate.weighted_average(a, b, a_weight)

        return None

    def get_start_time(self) -> datetime:
        return self.coordinates[0].timestamp

    def get_end_time(self) -> datetime:
        return self.coordinates[-1].timestamp

    def get_length(self) -> timedelta:
        return self.get_end_time() - self.get_start_time()


def calculate_segment_distance(
    garmin_segment: Segment,
    go_pro_segment: Segment,
    step: timedelta,
    go_pro_start_offset: timedelta,
) -> float:
    start_time = go_pro_segment.get_start_time()
    end_time = go_pro_segment.get_end_time()

    total_distance = 0.0
    num_points = 0
    while start_time <= end_time:
        garmin_coorindate = garmin_segment.get_coordinate(start_time)
        go_pro_coordinate = go_pro_segment.get_coordinate(
            start_time + go_pro_start_offset
        )

        if garmin_coorindate is None or go_pro_coordinate is None:
            if num_points != 0:
                break
            start_time += step
            continue

        total_distance += Coordinate.distance(garmin_coorindate, go_pro_coordinate)
        num_points += 1
        start_time += step

    return total_distance / num_points
