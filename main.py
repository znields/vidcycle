import gpxpy
import gpxpy.gpx
import argparse
import subprocess
from datetime import datetime, timezone
from moviepy import *


parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--gpx-file", help="GPX file of ride", required=True)
parser.add_argument("--video-file", help="Video file of ride", required=True)
args = vars(parser.parse_args())


def load_gpx_file():
    gpx_file = open(args["gpx_file"], "r")
    gpx = gpxpy.parse(gpx_file)
    return gpx


def get_data_from_gpx(gpx):
    coordinates = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append(
                    {
                        "time": point.time.timestamp(),
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "elevation": point.elevation,
                        "point": point,
                    }
                )
    coordinates = add_speed_to_coordinates(coordinates)
    coordinates = add_extension_data_to_coordinates(coordinates)
    return coordinates


def add_speed_to_coordinates(coordinates):
    first = coordinates[0]
    coordinates_with_speed = []
    for coordinate in coordinates:
        coordinates_with_speed.append(
            {
                "latitude": coordinate["latitude"] - first["latitude"],
                "longitude": coordinate["longitude"] - first["longitude"],
                "speed": 0.0
                if len(coordinates_with_speed) == 0
                else coordinate["point"].speed_between(
                    coordinates_with_speed[-1]["point"]
                ),
                **coordinate,
            }
        )
    return coordinates_with_speed


def add_extension_data_to_coordinates(coordinates):
    coordinates_with_metadata = []
    for coordinate in coordinates:
        extensions = coordinate["point"].extensions
        if len(extensions) == 1:
            power = 0
            temp, hr, cad = [int(ext.text) for ext in extensions[0]]
        else:
            power, other = extensions
            temp, hr, cad = [int(ext.text) for ext in other]
            power = int(power.text)

        coordinate = {**coordinate, "power": power, "temp": temp, "hr": hr, "cad": cad}
        del coordinate["point"]
        coordinates_with_metadata.append(coordinate)
    return coordinates_with_metadata


def fetch_mp4_exif_data():
    output = subprocess.run(
        ["exiftool", "-api", "largefilesupport=1", args["video_file"]],
        capture_output=True,
    )
    out = output.stdout
    out = [[str(j).strip() for j in i.split(":", 1)] for i in str(out).split("\\n")]
    out = [i for i in out if len(i) == 2]
    return dict(out)


def get_video_start_timestamp(exif_data):
    video_start_time = datetime.strptime(
        exif_data["Track Create Date"], "%Y:%m:%d %H:%M:%S"
    )
    video_start_time = video_start_time.replace(tzinfo=timezone.utc)
    return datetime.timestamp(video_start_time)


if __name__ == "__main__":
    data = fetch_mp4_exif_data()
    start_timestamp = get_video_start_timestamp(data)
    print(start_timestamp)

    gpx = load_gpx_file()
    data = [
        datum for datum in get_data_from_gpx(gpx) if datum["time"] > start_timestamp
    ]
    print(len(data))
