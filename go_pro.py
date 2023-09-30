import subprocess
import gpxpy
from typing import List, Tuple
from datetime import datetime, timezone, timedelta
from coordinate import Coordinate


def load_coordinates_from_file(video_file_path: str) -> List[Coordinate]:
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
            timestamp=point.time, latitude=point.latitude, longitude=point.longitude
        )
        for point in points
        if point.latitude != 0 and point.longitude != 0
    ]


def load_exif_data(video_file_path: str):
    output = subprocess.run(
        ["exiftool", "-api", "largefilesupport=1", video_file_path],
        capture_output=True,
    )
    out = output.stdout
    out = [[str(j).strip() for j in i.split(":", 1)] for i in str(out).split("\\n")]
    out = [i for i in out if len(i) == 2]
    return dict(out)


def get_start_and_end_time(video_file_path: str) -> Tuple[datetime, datetime]:
    exif_data = load_exif_data(video_file_path)
    video_start_time = datetime.strptime(
        exif_data["Track Create Date"], "%Y:%m:%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    track_duration = datetime.strptime(exif_data["Track Duration"], "%H:%M:%S")
    track_duration = timedelta(
        hours=track_duration.hour,
        minutes=track_duration.minute,
        seconds=track_duration.second,
    )
    return (
        video_start_time,
        video_start_time + track_duration,
    )
