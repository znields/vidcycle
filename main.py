import argparse
from coordinate import GarminSegment
from datetime import timedelta
from render import ThreadedPanelRenderer, VideoRenderer
from video import GoProVideo

parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--fit-file", help="GPX file of ride", required=True, type=str)
parser.add_argument("--video-file", help="Video file of ride", required=True, type=str)
parser.add_argument(
    "--video-stats-refresh-rate-in-secs",
    help="How often the video stats refresh in seconds",
    default=0.1,
    type=float,
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
    type=str,
    required=True,
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
    video_offset = timedelta(seconds=args["video_offset_start_in_secs"])
    video_stats_refresh_rate = timedelta(
        seconds=args["video_stats_refresh_rate_in_secs"]
    )

    video = GoProVideo(args["video_file"])

    video_length = (
        timedelta(seconds=args["video_length_in_secs"])
        if args["video_length_in_secs"] is not None
        else video.get_duration()
    )

    garmin_segment = GarminSegment.load_from_fit_file(args["fit_file"])

    left_search, right_search = (
        video.get_start_time() + first_move_time + left_search_bound,
        video.get_start_time() + first_move_time + right_search_bound,
    )
    print(
        f"Searching for first Garmin move time between {left_search} and {right_search}."
    )
    garmin_first_move_coordinate = garmin_segment.get_first_move_coordinate(
        left_search, right_search
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
    go_pro_first_move_time = video.get_start_time() + first_move_time

    garmin_time_shift = garmin_first_move_time - go_pro_first_move_time

    garmin_start_time = video.get_start_time() + video_offset + garmin_time_shift

    ThreadedPanelRenderer(
        segment=garmin_segment,
        segment_start_time=garmin_start_time,
        video_length=video_length,
        video=video,
        output_folder="panel",
        frames_per_second=30,
        panel_width=0.2,
        map_height=0.3,
        map_opacity=0.9,
        map_marker_size=15,
        stat_keys_and_labels=[
            ("power", "PWR"),
            ("speed", "MPH"),
            ("heart_rate", "HR"),
            ("cadence", "RPM"),
        ],
        stats_x_position=0.15,
        stats_y_range=(0.05, 0.7),
        stat_label_y_position_delta=0.11,
        stats_opacity=0.9,
        num_threads=116,
    ).render()

    VideoRenderer(video=video, panel_folder="panel", output_filepath="out.mp4").render()
