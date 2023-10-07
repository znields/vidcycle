from moviepy import *
from moviepy.editor import *
from datetime import datetime
from coordinate import Segment, GarminCoordinate
from typing import List


def write_video(
    in_video_path: str,
    out_video_path: str,
    render_height: int,
    video_start_time: datetime,
    video_end_time: datetime,
    coordinates: List[GarminCoordinate],
    stats_refresh_period_in_seconds: int = 0.5,
) -> None:
    clip = VideoFileClip(in_video_path).resize(height=render_height)
    # TODO pull subclips

    stat_clips = [
        concatenate_videoclips(
            [
                TextClip(str(coordinate[key]), fontsize=70, color="white").set_duration(
                    stats_refresh_period_in_seconds
                )
                for coordinate in coordinates
            ]
        )
        .subclip(0, subclip_range[1] - subclip_range[0])
        .set_position((0.01, idx / 10), relative=True)
        for idx, key in enumerate(
            ["time", "power", "hr", "cad", "elevation", "latitude", "longitude"], 1
        )
    ]

    # video = CompositeVideoClip([clip] + stat_clips)

    # video.write_videofile(out_video_path)


def get_stats_clip(garmin_segment: Segment, stats_refresh_period_in_seconds: int):
    pass
