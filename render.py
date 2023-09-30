from moviepy import *
from moviepy.editor import *
from datetime import datetime
from coordinate import Segment


def write_video(
    in_video_path: str,
    out_video_path: str,
    render_height: int,
    video_start_time: datetime,
    video_end_time: datetime,
    garmin_segment: Segment,
) -> None:
    clip = VideoFileClip(in_video_path).resize(height=render_height)
    # TODO pull subclips

    # stat_clips = [
    #     concatenate_videoclips(
    #         [
    #             TextClip(str(coordinate[key]), fontsize=70, color="white").set_duration(
    #                 coordinate["duration"]
    #             )
    #             for coordinate in coordinates
    #         ]
    #     )
    #     .subclip(0, subclip_range[1] - subclip_range[0])
    #     .set_position((0.01, idx / 10), relative=True)
    #     for idx, key in enumerate(
    #         ["time", "power", "hr", "cad", "elevation", "latitude", "longitude"], 1
    #     )
    # ]

    # video = CompositeVideoClip([clip] + stat_clips)

    # video.write_videofile(out_video_path)
