from datetime import datetime, timedelta, timezone
import json
from typing import List, Optional, Dict, Any, Tuple
import geopy.distance
import functools
from garmin_fit_sdk import Decoder, Stream
import subprocess
import gpxpy
import csv
from copy import copy


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

    def __copy__(self) -> "Coordinate":
        return type(self)(self.timestamp, self.latitude, self.longitude)

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=4, default=str)

    def set_timestamp(self, timestamp: datetime):
        self.timestamp = timestamp

    def weighted_average(
        self, other_coordinate: "Coordinate", other_weight: float
    ) -> "Coordinate":
        assert 0.0 <= other_weight <= 1.0
        self_weight = 1.0 - other_weight

        return Coordinate(
            timestamp=datetime.fromtimestamp(
                (self.timestamp.timestamp() * self_weight)
                + (other_coordinate.timestamp.timestamp() * other_weight),
                tz=self.timestamp.tzinfo,
            ),
            latitude=(self.latitude * self_weight)
            + (other_coordinate.latitude * other_weight),
            longitude=(self.longitude * self_weight)
            + (other_coordinate.longitude * other_weight),
        )

    def distance(self, other: "Coordinate") -> "Coordinate":
        return geopy.distance.geodesic(
            (self.latitude, self.longitude), (other.latitude, other.longitude)
        ).km

    @staticmethod
    def load_coordinates_from_video_file(video_file_path: str) -> List["Coordinate"]:
        output = subprocess.run(
            [
                "exiftool",
                "-ee",
                "-p",
                "gpx.fmt",
                "-api",
                "largefilesupport=1",
                video_file_path,
            ],
            capture_output=True,
        )
        out = output.stdout
        gpx = gpxpy.parse(out)
        points = gpx.tracks[0].segments[0].points
        return [
            Coordinate(
                timestamp=point.time,
                latitude=point.latitude,
                longitude=point.longitude,
            )
            for point in points
            if point.latitude != 0 and point.longitude != 0
        ]


class GarminCoordinate(Coordinate):
    INT_TO_FLOAT_LAT_LONG_CONST = 11930465

    def __init__(
        self,
        timestamp: datetime,
        distance: float,
        altitude: float,
        temperature: int,
        heart_rate: Optional[int] = None,
        speed: Optional[float] = None,
        position_lat: Optional[int] = None,
        position_long: Optional[int] = None,
        power: Optional[int] = None,
        cadence: Optional[int] = None,
        **_kwargs: Dict[str, Any]
    ):
        self.position_lat = position_lat
        self.position_long = position_long

        if position_lat is not None:
            position_lat /= self.INT_TO_FLOAT_LAT_LONG_CONST
        if position_long is not None:
            position_long /= self.INT_TO_FLOAT_LAT_LONG_CONST

        super().__init__(timestamp, position_lat, position_long)

        self.distance = distance
        self.altitude = altitude
        self.speed = speed
        self.heart_rate = heart_rate
        self.temperature = temperature
        self.power = power
        self.cadence = cadence

    def __copy__(self) -> "GarminCoordinate":
        return type(self)(
            self.timestamp,
            self.distance,
            self.altitude,
            self.temperature,
            self.heart_rate,
            self.speed,
            self.position_lat,
            self.position_long,
            self.power,
            self.cadence,
        )

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=4, default=str)

    def weighted_average(
        self, other_coordinate: "GarminCoordinate", other_weight: float
    ) -> "GarminCoordinate":
        super_coordinate = super().weighted_average(other_coordinate, other_weight)
        kwargs = {
            "timestamp": super_coordinate.timestamp,
            "position_long": super_coordinate.longitude
            * self.INT_TO_FLOAT_LAT_LONG_CONST,
            "position_lat": super_coordinate.latitude
            * self.INT_TO_FLOAT_LAT_LONG_CONST,
        }

        self_weight = 1.0 - other_weight

        other_dict = other_coordinate.__dict__
        self_dict = self.__dict__
        for key in self_dict:
            if (
                key in ["latitude", "longitude", "timestamp"]
                or other_dict[key] is None
                or self_dict[key] is None
            ):
                continue
            kwargs[key] = (self_dict[key] * self_weight) + (
                other_dict[key] * other_weight
            )

        garmin_coordinate = GarminCoordinate(**kwargs)

        return garmin_coordinate


class Segment:
    def __init__(self, coordinates: List[Coordinate]) -> None:
        self.coordinates: List[Coordinate] = self._get_filtered_coordinates(coordinates)

    def _get_filtered_coordinates(
        self, coordinates: List[Coordinate]
    ) -> List[Coordinate]:
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
        return reversed_coordinates[::-1]

    # TODO: optimize using binary search
    @functools.lru_cache(maxsize=None)
    def get_coordinate(self, time: datetime) -> Optional[Coordinate]:
        result = None

        for a, b in zip(self.coordinates[:-1], self.coordinates[1:]):
            if a.timestamp <= time <= b.timestamp:
                a_timestamp = a.timestamp.timestamp()
                b_timestamp = b.timestamp.timestamp()

                time_delta = b_timestamp - a_timestamp
                # why care if there is a gap > 1.5 secs?
                # because this indicates gps stopped recording
                if time_delta < 0.0001 or time_delta > 1.5:
                    result = copy(a)
                    break

                weight = (b_timestamp - time.timestamp()) / (b_timestamp - a_timestamp)
                result = a.weighted_average(b, 1.0 - weight)
                break

        if result is not None:
            result.set_timestamp(time)

        return result

    def get_start_time(self) -> datetime:
        return self.coordinates[0].timestamp

    def get_end_time(self) -> datetime:
        return self.coordinates[-1].timestamp

    def get_length(self) -> timedelta:
        return self.get_end_time() - self.get_start_time()

    def get_iterator(self, iterator_step_length: timedelta):
        return SegmentIterator(self, iterator_step_length)

    def _get_coordinates(
        self, start_time: datetime, end_time: datetime, step_length: timedelta
    ) -> List[Coordinate]:
        new_coordinates = []
        while start_time <= end_time:
            new_coordinates.append(self.get_coordinate(start_time))
            start_time += step_length
        return new_coordinates

    def get_subsegment(
        self, start_time: datetime, end_time: datetime, step_length: timedelta
    ) -> "Segment":
        new_coordinates: List[Coordinate] = self._get_coordinates(
            start_time, end_time, step_length
        )
        return Segment(new_coordinates)

    def write_to_csv(self, file_path):
        with open(file_path, "w") as csvfile:
            writer = csv.writer(csvfile)

            for coordinate in self.coordinates:
                writer.writerow(
                    [
                        int(coordinate.timestamp.timestamp()),
                        coordinate.latitude,
                        coordinate.longitude,
                    ]
                )

        csvfile.close()

    def get_xy_pair(self) -> Tuple[float, float]:
        return 0.0, 0.0


class GarminSegment(Segment):
    def get_coordinate(self, time: datetime) -> Optional[GarminCoordinate]:
        return super().get_coordinate(time)

    def __init__(self, coordinates: List[GarminCoordinate]) -> None:
        super().__init__(coordinates)
        self.coordinates: List[GarminCoordinate] = self.coordinates

    def write_to_csv(self, file_path):
        with open(file_path, "w") as csvfile:
            writer = csv.writer(csvfile)

            for coordinate in self.coordinates:
                writer.writerow(
                    [
                        int(coordinate.timestamp.timestamp()),
                        coordinate.latitude,
                        coordinate.longitude,
                        coordinate.speed,
                    ]
                )

        csvfile.close()

    def get_iterator(self, iterator_step_length: timedelta):
        return GarminSegmentIterator(self, iterator_step_length)

    def get_subsegment(
        self, start_time: datetime, end_time: datetime, step_length: timedelta
    ) -> "GarminSegment":
        new_coordinates: List[GarminCoordinate] = self._get_coordinates(
            start_time, end_time, step_length
        )
        return GarminSegment(new_coordinates)

    def get_first_move_coordinate(
        self, start_time: datetime, end_time: datetime
    ) -> Optional[GarminCoordinate]:
        for a, b in zip(self.coordinates[:-1], self.coordinates[1:]):
            if not start_time < a.timestamp < b.timestamp < end_time:
                continue

            if (a.speed is None or a.speed < 0.0001) and (
                b.speed is not None and b.speed > 0.0001
            ):
                return b

        return None

    @staticmethod
    def load_from_fit_file(path: str) -> List["GarminCoordinate"]:
        stream = Stream.from_file(path)

        decoder = Decoder(stream)
        messages, _ = decoder.read()

        coordinates = []
        for message in messages["record_mesgs"]:
            message = {key: message[key] for key in message if type(key) == str}
            coordinates.append(GarminCoordinate(**message))
        return GarminSegment(coordinates)


class SegmentIterator:
    def __init__(self, segment: Segment, iterator_step_length: timedelta) -> None:
        self.segment = segment
        self.iterator_step_length = iterator_step_length
        self.iterator_time = self.segment.get_start_time()

    def __iter__(self):
        self.iterator_time = self.segment.get_start_time()
        return self

    def __next__(self) -> Coordinate:
        coordinate = self.segment.get_coordinate(self.iterator_time)
        self.iterator_time += self.iterator_step_length

        if coordinate is None:
            raise StopIteration

        return coordinate


class GarminSegmentIterator(SegmentIterator):
    def __init__(self, segment: GarminSegment, iterator_step_length: timedelta):
        super().__init__(segment, iterator_step_length)

    def __iter__(self) -> "GarminSegmentIterator":
        return super().__iter__()

    def __next__(self) -> GarminCoordinate:
        return super().__next__()


def calculate_segment_distance(
    garmin_segment: GarminSegment,
    go_pro_segment: Segment,
    go_pro_start_offset: timedelta,
    gps_align_step_size: timedelta,
) -> float:
    total_distance = 0.0
    num_points = 0

    for go_pro_coordinate in go_pro_segment.get_iterator(gps_align_step_size):
        garmin_coorindate = garmin_segment.get_coordinate(
            go_pro_coordinate.timestamp + go_pro_start_offset
        )
        if garmin_coorindate.speed is None or garmin_coorindate.speed < 0.1:
            continue

        if garmin_coorindate is None:
            if num_points != 0:
                break
            continue

        total_distance += Coordinate.distance(garmin_coorindate, go_pro_coordinate)
        num_points += 1

    return total_distance / num_points if num_points != 0 else float("inf")
