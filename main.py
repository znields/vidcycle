import argparse
import go_pro
from coordinate import Segment, calculate_segment_distance, GarminCoordinate, Coordinate
from datetime import timedelta
from tqdm import tqdm
from numpy import arange
import render
from typing import Optional

parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--fit-file", help="GPX file of ride", required=True)
parser.add_argument("--video-file", help="Video file of ride", required=True)
parser.add_argument(
    "--gps-align-explore-range-in-secs",
    help="Range of number of seconds to search for GPS alignment (low -> high)",
    nargs=2,
    type=float,
    required=True,
)
parser.add_argument(
    "--gps-align-step-size-in-secs",
    help="Step size for gps alignment in seconds",
    default=0.5,
    type=float,
    required=True,
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
    required=True,
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
args = vars(parser.parse_args())


if __name__ == "__main__":
    garmin_coordinates = GarminCoordinate.load_coordinates_from_fit_file(
        args["fit_file"]
    )
    go_pro_coordinates = Coordinate.load_coordinates_from_video_file(args["video_file"])

    go_pro_start_time, _ = go_pro.get_start_and_end_time(args["video_file"])

    garmin_segment = Segment(garmin_coordinates)
    go_pro_segment = Segment(go_pro_coordinates)

    min_segment_distance = float("inf")
    best_shift_in_seconds = args["gps_align_explore_range_in_secs"][0]

    for shift_seconds in tqdm(
        arange(
            *args["gps_align_explore_range_in_secs"],
            args["gps_align_step_size_in_secs"],
        )
    ):
        segment_distance = calculate_segment_distance(
            garmin_segment,
            go_pro_segment,
            timedelta(seconds=shift_seconds),
            timedelta(seconds=args["gps_align_step_size_in_secs"]),
        )
        if min_segment_distance >= segment_distance:
            min_segment_distance = segment_distance
            best_shift_in_seconds = shift_seconds

    print(
        f"Based on GPS data Garmin is {abs(best_shift_in_seconds)} seconds {'ahead of' if best_shift_in_seconds > 0 else 'behind'} GoPro"
    )
    print(
        f"Average GPS distance between Garmin and GoPro is {min_segment_distance * 1000:.2f} meters"
    )
    best_shift = timedelta(seconds=best_shift_in_seconds)

    video_length = timedelta(seconds=args["video_length_in_secs"])
    video_offset = timedelta(seconds=args["video_offset_start_in_secs"])
    video_stats_refresh_rate = timedelta(
        seconds=args["video_stats_refresh_rate_in_secs"]
    )

    video_start_time = go_pro_start_time + best_shift + video_offset
    video_end_time = video_start_time + video_length

    render.write_video(
        args["video_file"],
        args["video_output_path"],
        garmin_segment,
        video_start_time,
        video_end_time,
        video_length,
        video_offset,
        video_stats_refresh_rate,
    )
