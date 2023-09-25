import gpxpy
import gpxpy.gpx
import argparse
import subprocess
from datetime import datetime, timezone
from moviepy import *
from moviepy.editor import *


parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--gpx-file", help="GPX file of ride", required=True)
parser.add_argument("--video-file", help="Video file of ride", required=True)
parser.add_argument(
    "--output-start",
    help="Starting time of output video in seconds",
    default=0,
    type=int,
)
parser.add_argument(
    "--output-length",
    help="Length of video output in seconds",
    default=None,
    type=int,
)
args = vars(parser.parse_args())


def load_gpx_file():
    gpx_file = open(args["gpx_file"], "r")
    gpx = gpxpy.parse(gpx_file)
    return gpx


def get_coordinates_from_gpx(gpx):
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
    coordinates = add_duration_to_coordinates(coordinates)
    coordinates = add_extension_data_to_coordinates(coordinates)
    return coordinates


def add_speed_to_coordinates(coordinates):
    first = coordinates[0]
    coordinates_with_speed = []
    for coordinate in coordinates:
        coordinates_with_speed.append(
            {
                **coordinate,
                "speed": 0.0
                if len(coordinates_with_speed) == 0
                else coordinate["point"].speed_between(
                    coordinates_with_speed[-1]["point"]
                ),
            }
        )
    return coordinates_with_speed


def add_duration_to_coordinates(coordinates):
    for idx, pair in enumerate(zip(coordinates, coordinates[1:])):
        curr, next = pair
        coordinates[idx]["duration"] = next["time"] - curr["time"]

    coordinates[-1]["duration"] = 1
    return coordinates


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


def get_video_start_and_end_timestamp(exif_data):
    video_start_time = datetime.strptime(
        exif_data["Track Create Date"], "%Y:%m:%d %H:%M:%S"
    )
    hours, minutes, seconds = [int(i) for i in exif_data["Track Duration"].split(":")]
    video_start_time = video_start_time.replace(tzinfo=timezone.utc)
    start_timestamp = datetime.timestamp(video_start_time)
    return start_timestamp, start_timestamp + (hours * 3600) + (minutes * 60) + seconds


def adjust_start_and_end_timestamp(start, end):
    adjusted_start_timestamp = start + args["output_start"]

    if args["output_length"] is not None:
        adjusted_end_timestamp = adjusted_start_timestamp + args["output_length"]
    else:
        adjusted_end_timestamp = end

    return adjusted_start_timestamp, adjusted_end_timestamp


def get_video_time_range(start_timestamp, end_timestamp):
    subclip_start = args["output_start"]
    if args["output_length"] is None:
        subclip_end = (end_timestamp - start_timestamp) - args["output_start"]
    else:
        subclip_end = args["output_start"] + (
            args["output_length"] if args["output_length"] is not None else 0
        )
    return subclip_start, subclip_end


def filter_coordinates_and_fix_edge_coordinates(
    coordinates, adjusted_start_timestamp, adjusted_end_timestamp
):
    filtered_coordinates = []
    for coordinate in coordinates:
        if adjusted_end_timestamp >= coordinate["time"] >= adjusted_start_timestamp:
            filtered_coordinates.append(coordinate)
        elif True:
            pass

    return filtered_coordinates


if __name__ == "__main__":
    exif_data = fetch_mp4_exif_data()
    start_timestamp, end_timestamp = get_video_start_and_end_timestamp(exif_data)

    adjusted_start_timestamp, adjusted_end_timestamp = adjust_start_and_end_timestamp(
        start_timestamp, end_timestamp
    )

    gpx_data = load_gpx_file()

    coordinates = get_coordinates_from_gpx(gpx_data)

    print(
        f"Found {len(coordinates)} coordinates between times {adjusted_start_timestamp} "
        f"and {adjusted_end_timestamp} ({adjusted_end_timestamp - adjusted_start_timestamp} seconds)"
    )

    subclip_range = get_video_time_range(
        start_timestamp,
        end_timestamp,
    )

    print(
        f"Clipping {subclip_range[1] - subclip_range[0]} seconds of video from {subclip_range[0]} "
        f"to {subclip_range[1]}"
    )

    clip = VideoFileClip(args["video_file"]).subclip(*subclip_range)

    text_clip = concatenate_videoclips(
        [
            TextClip(str(coordinate["time"]), fontsize=70, color="white")
            .set_pos(("right", "top"))
            .set_duration(coordinate["duration"])
            for coordinate in coordinates
        ]
    ).subclip(0, subclip_range[1] - subclip_range[0])

    video = CompositeVideoClip([clip, text_clip])

    video.write_videofile("out.mp4")
