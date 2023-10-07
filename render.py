from moviepy import *
from moviepy.editor import *
from datetime import datetime
from coordinate import Segment, GarminCoordinate
from typing import List


def write_video(
    in_video_path: str,
    out_video_path: str,
    render_height: int,
    video_segment: Segment,
    video_length: float,
    video_offset: float,
) -> None:
    clip = (
        VideoFileClip(in_video_path)
        .resize(height=render_height)
        .subclip(video_offset, video_offset + video_length)
    )

    stat_clips = []
    for idx, key in enumerate(
        [
            "timestamp",
            "speed",
            "power",
            "heart_rate",
            "cadence",
            "altitude",
            "latitude",
            "longitude",
        ],
        1,
    ):
        text_clips = []
        for coordinate in video_segment:
            text_clip = TextClip(
                str(coordinate.__dict__[key]), fontsize=70, color="white"
            ).set_duration(video_segment.iterator_step_length.total_seconds())
            text_clips.append(text_clip)

        stat_clip = (
            concatenate_videoclips(text_clips)
            .set_position((0.01, idx / 10), relative=True)
            .subclip(0, video_length)
        )

        stat_clips.append(stat_clip)

    video = CompositeVideoClip([clip] + stat_clips)

    video.write_videofile(out_video_path)
