import argparse
from coordinate import GarminSegment
from datetime import timedelta
from render import ThreadedPanelRenderer, VideoRenderer
from video import GoProVideo
import time
import json

parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--fit-file", help="FIT file of ride", required=True, type=str)
parser.add_argument("--video-file", help="Video file of ride", required=True, type=str)
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
    "--video-lap-time-in-secs",
    help="Lap time in seconds from the video.",
    required=True,
    type=float,
)
parser.add_argument(
    "--lap-time-search-window-in-secs",
    help="Search window for lap time.",
    required=True,
    type=float,
    nargs=2,
)
parser.add_argument(
    "--render-config-file",
    help="Render config file to determine video render style",
    required=True,
    type=str,
)
args = vars(parser.parse_args())


if __name__ == "__main__":
    video_output_path = args["video_output_path"]
    left_search_bound = timedelta(seconds=args["lap_time_search_window_in_secs"][0])
    right_search_bound = timedelta(seconds=args["lap_time_search_window_in_secs"][1])
    lap_time = timedelta(seconds=args["video_lap_time_in_secs"])
    video_offset = timedelta(seconds=args["video_offset_start_in_secs"])

    video = GoProVideo(args["video_file"])

    video_length = (
        timedelta(seconds=args["video_length_in_secs"])
        if args["video_length_in_secs"] is not None
        else video.get_duration()
    )

    render_config_file = open(args["render_config_file"])
    render_config = json.loads(render_config_file.read())

    garmin_segment = GarminSegment.load_from_fit_file(args["fit_file"])

    print(f"Video start:   {str(video.get_start_time())}")
    print(f"Video end:     {str(video.get_end_time())}")
    print(f"Garmin start:  {str(garmin_segment.get_start_time())}")
    print(f"Garmin end:    {str(garmin_segment.get_end_time())}\n")

    left_search, right_search = (
        video.get_start_time() + lap_time + left_search_bound,
        video.get_start_time() + lap_time + right_search_bound,
    )

    print("Available lap timestamps:\n")
    print(
        "\n".join([str(lap.timestamp) for lap in garmin_segment.get_manual_laps()])
        + "\n"
    )
    print(f"Searching for Garmin lap time between {left_search} and {right_search}.")
    garmin_lap = garmin_segment.get_first_lap(left_search, right_search)

    if garmin_lap is None:
        print(
            "Could not find lap coordinate. There must be one to align video. Exiting."
        )
        exit()
    else:
        print(f"Found Garmin lap time at {garmin_lap.timestamp}.\n")

    garmin_lap_time = garmin_lap.timestamp
    go_pro_lap_time = video.get_start_time() + lap_time

    garmin_time_shift = garmin_lap_time - go_pro_lap_time

    garmin_start_time = video.get_start_time() + video_offset + garmin_time_shift
    print(f"Garmin time shift: {garmin_time_shift}")
    print(f"Garmin start time: {garmin_start_time}\n")

    print("Rendering side panels...")

    render_start_time = time.time()

    ThreadedPanelRenderer(
        segment=garmin_segment,
        segment_start_time=garmin_start_time,
        video_length=video_length,
        video=video,
        output_folder="panel",
        num_threads=render_config["panelNumberOfThreads"],
        panel_width=render_config["panelWidth"],
        map_height=render_config["map"]["height"],
        map_opacity=render_config["map"]["opacity"],
        map_marker_inner_size=render_config["map"]["marker"]["innerSize"],
        map_marker_inner_opacity=render_config["map"]["marker"]["innerOpacity"],
        map_marker_outer_size=render_config["map"]["marker"]["outerSize"],
        map_marker_outer_opacity=render_config["map"]["marker"]["outerOpacity"],
        stat_keys_and_labels=render_config["stats"]["keysAndLabels"],
        stats_x_position=render_config["stats"]["xPosition"],
        stats_y_range=render_config["stats"]["yPositionRange"],
        stat_label_y_position_delta=render_config["stats"]["statToLabelYDistance"],
        stats_opacity=render_config["stats"]["opacity"],
    ).render()

    print("Rendering video...")

    VideoRenderer(
        video=video,
        panel_folder="panel",
        output_filepath=video_output_path,
        num_threads=render_config["videoNumberOfThreads"],
        video_length=video_length,
        video_offset=video_offset,
    ).render()

    print(f"\nTotal render time: {time.time() - render_start_time} seconds.")
