import argparse
from moviepy import *
from moviepy.editor import *
import go_pro
from coordinate import Segment, calculate_segment_distance, GarminCoordinate, Coordinate
from datetime import timedelta
from tqdm import tqdm
from numpy import arange

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
args = vars(parser.parse_args())


if __name__ == "__main__":
    garmin_coordinates = GarminCoordinate.load_coordinates_from_fit_file(
        args["fit_file"]
    )
    go_pro_coordinates = Coordinate.load_coordinates_from_video_file(args["video_file"])

    start, end = go_pro.get_start_and_end_time(args["video_file"])

    garmin_segment = Segment(garmin_coordinates)
    go_pro_segment = Segment(go_pro_coordinates)

    min_segment_distance = float("inf")
    best_shift_in_seconds = None  # TODO: improve name

    for shift_seconds in tqdm(
        arange(
            *args["gps_align_explore_range_in_secs"],
            args["gps_align_step_size_in_secs"]
        )
    ):
        segment_distance = calculate_segment_distance(
            garmin_segment,
            go_pro_segment,
            timedelta(seconds=0.5),
            timedelta(seconds=shift_seconds),
        )
        if min_segment_distance >= segment_distance:
            min_segment_distance = segment_distance
            best_shift_in_seconds = shift_seconds

    print(min_segment_distance, best_shift_in_seconds)
