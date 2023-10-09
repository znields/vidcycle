import argparse
import go_pro
from coordinate import (
    GarminSegment,
    GarminCoordinate,
)
from datetime import timedelta
import render

parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--fit-file", help="GPX file of ride", required=True, type=str)
parser.add_argument("--video-file", help="Video file of ride", required=True, type=str)
parser.add_argument(
    "--optimized-video-resolution",
    help="Video resolution of optimized video",
    type=int,
    default=None,
)
parser.add_argument(
    "--video-stats-refresh-rate-in-secs",
    help="How often the video stats refresh in seconds",
    default=0.5,
    type=float,
    required=True,
)
parser.add_argument(
    "--video-length-in-secs",
    help="How many seconds the video should last",
    type=float,
    default=None,
)
parser.add_argument(
    "--video-offset-start-in-secs",
    help="How many seconds into the video should the output start",
    default=0.0,
    type=float,
)
parser.add_argument(
    "--video-output-path",
    help="Video output path. If none then will preview video.",
    default=None,
    type=str,
)
parser.add_argument(
    "--first-move-time-in-secs",
    help="First move time in video in seconds.",
    required=True,
    type=float,
)
parser.add_argument(
    "--first-move-time-gps-search-window-in-secs",
    help="First move time range of search window.",
    required=True,
    type=float,
    nargs=2,
)
args = vars(parser.parse_args())


if __name__ == "__main__":
    left_search_bound = timedelta(
        seconds=args["first_move_time_gps_search_window_in_secs"][0]
    )
    right_search_bound = timedelta(
        seconds=args["first_move_time_gps_search_window_in_secs"][1]
    )
    first_move_time = timedelta(seconds=args["first_move_time_in_secs"])

    video_length = (
        timedelta(seconds=args["video_length_in_secs"])
        if args["video_length_in_secs"] is not None
        else None
    )
    video_offset = timedelta(seconds=args["video_offset_start_in_secs"])
    video_stats_refresh_rate = timedelta(
        seconds=args["video_stats_refresh_rate_in_secs"]
    )

    go_pro_start_time, _ = go_pro.get_start_and_end_time(args["video_file"])
    if args["optimized_video_resolution"] is not None:
        optimized_video_file_path = render.write_optimized_video(
            args["video_file"], args["optimized_video_resolution"]
        )
    else:
        optimized_video_file_path = args["video_file"]

    garmin_coordinates = GarminCoordinate.load_coordinates_from_fit_file(
        args["fit_file"]
    )
    garmin_segment = GarminSegment(garmin_coordinates)

    left_search, right_search = (
        go_pro_start_time + first_move_time + left_search_bound,
        go_pro_start_time + first_move_time + right_search_bound,
    )
    print(
        f"Searching for first Garmin move time between {left_search} and {right_search}."
    )
    garmin_first_move_coordinate = garmin_segment.get_first_move_coordinate(
        go_pro_start_time + first_move_time + left_search_bound,
        go_pro_start_time + first_move_time + right_search_bound,
    )

    if garmin_first_move_coordinate is None:
        print(
            "Could not find first move coordinate. There must be one to align video. Exiting."
        )
        exit()
    else:
        print(
            f"Found first Garmin move time at {garmin_first_move_coordinate.timestamp}."
        )

    garmin_first_move_time = garmin_first_move_coordinate.timestamp
    go_pro_first_move_time = go_pro_start_time + first_move_time

    garmin_time_shift = garmin_first_move_time - go_pro_first_move_time

    garmin_start_time = go_pro_start_time + video_offset + garmin_time_shift

    render.write_video(
        args["video_file"],
        optimized_video_file_path,
        args["video_output_path"],
        args["optimized_video_resolution"],
        garmin_segment,
        garmin_start_time,
        video_length,
        video_offset,
        video_stats_refresh_rate,
    )
