from moviepy import *
from moviepy.editor import *
from datetime import timedelta, datetime
from coordinate import GarminSegment
import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from typing import Optional
from typing import Any
import os

FRAME_PER_SECOND = 30
DEFAULT_FONT_SIZE = 190


def write_video(
    original_in_video_path: str,
    in_video_path: str,
    out_video_path: Optional[str],
    optimized_video_resolution: Optional[int],
    garmin_segment: GarminSegment,
    garmin_start_time: datetime,
    garmin_end_time: datetime,
    video_length: timedelta,
    video_offset: timedelta,
    stats_refresh_period: timedelta,
) -> None:
    clip = VideoFileClip(in_video_path).subclip(
        video_offset.total_seconds(),
        video_offset.total_seconds() + video_length.total_seconds(),
    )

    if optimized_video_resolution is not None:
        scale_factor = (
            optimized_video_resolution / VideoFileClip(original_in_video_path).size[1]
        )
    else:
        scale_factor = 1.0

    garmin_subsegment = garmin_segment.get_subsegment(
        garmin_start_time, garmin_end_time, stats_refresh_period
    )

    MAP_AND_LOCATION_CLIP_SIZE = 0.75 * scale_factor
    MAP_AND_LOCATION_POSITION = (0.01, 0.05)
    LOCATION_POINT_SIZE = 15 * scale_factor

    stat_clips = get_stat_clips(
        garmin_subsegment, video_length, stats_refresh_period, scale_factor
    )

    map_clip = (
        get_map_clip(
            garmin_segment,
            video_length,
            stats_refresh_period,
        )
        .set_opacity(0.75)
        .set_position(MAP_AND_LOCATION_POSITION, relative=True)
        .resize(MAP_AND_LOCATION_CLIP_SIZE)
    )

    location_clip_inner = (
        get_location_clip(
            garmin_segment,
            video_length,
            garmin_start_time,
            stats_refresh_period,
            LOCATION_POINT_SIZE,
        )
        .set_opacity(0.75)
        .set_position(MAP_AND_LOCATION_POSITION, relative=True)
        .resize(MAP_AND_LOCATION_CLIP_SIZE)
    )

    location_clip_outer = (
        get_location_clip(
            garmin_segment,
            video_length,
            garmin_start_time,
            stats_refresh_period,
            LOCATION_POINT_SIZE * 2,
        )
        .set_opacity(0.3)
        .set_position(MAP_AND_LOCATION_POSITION, relative=True)
        .resize(MAP_AND_LOCATION_CLIP_SIZE)
    )

    video = CompositeVideoClip(
        [clip, map_clip, location_clip_inner, location_clip_outer] + stat_clips
    )

    if out_video_path is None:
        video.without_audio().preview(fps=FRAME_PER_SECOND)
    else:
        video.write_videofile(out_video_path, fps=FRAME_PER_SECOND)


def get_stat_clips(
    garmin_segment: GarminSegment,
    video_length: timedelta,
    stats_refresh_period: timedelta,
    scale_factor: float,
):
    def data_to_str(data: Any):
        if data is None:
            return "0"

        if type(data) == float:
            return str(int(data))

        return str(data)

    stat_clips = []
    for idx, key_and_label in enumerate(
        [
            ("speed", "MPH"),
            ("power", "PWR"),
            ("cadence", "RPM"),
        ],
        2,
    ):
        key, label = key_and_label
        text_clips = []
        for coordinate in garmin_segment.get_iterator(stats_refresh_period):
            text_clip = (
                TextClip(
                    data_to_str(coordinate.__dict__[key])
                    + ("" if label is None else "\n" + label),
                    fontsize=DEFAULT_FONT_SIZE * scale_factor,
                    color="white",
                    font="Helvetica-Bold",
                )
                .set_duration(stats_refresh_period.total_seconds())
                .set_opacity(0.75)
            )
            text_clips.append(text_clip)

        stat_clip = (
            concatenate_videoclips(text_clips)
            .set_position((0.01, idx / 6), relative=True)
            .subclip(0, video_length.total_seconds())
        )

        stat_clips.append(stat_clip)
    return stat_clips


# TODO: add option to render only part of map
def get_map_clip(
    garmin_segment: GarminSegment,
    video_length: timedelta,
    stats_refresh_period: timedelta,
):
    fig_mpl = plt.figure(frameon=False, facecolor="black")
    ax = fig_mpl.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")

    verts = [
        (c.longitude, c.latitude)
        for c in garmin_segment.get_iterator(stats_refresh_period)
    ]
    codes = [Path.MOVETO] + [Path.CURVE3 for _ in range(len(verts) - 1)]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, edgecolor="white", facecolor="none", lw=6)
    ax.add_patch(patch)

    xs = [vert[0] for vert in verts]
    ys = [vert[1] for vert in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx, dy = max_x - min_x, max_y - min_y
    ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
    ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

    def make_frame_mpl(t):
        t = timedelta(seconds=t)

        frame = mplfig_to_npimage(fig_mpl)

        return frame

    def make_mask_mpl(t):
        t = timedelta(seconds=t)

        frame = make_frame_mpl(t.total_seconds())
        x, y, _ = frame.shape
        mask = (np.sum(frame, axis=2) > 10).reshape(x, y, 1)
        return mask

    mask = VideoClip(make_mask_mpl, duration=video_length.total_seconds(), ismask=True)
    clip = VideoClip(make_frame_mpl, duration=video_length.total_seconds())

    return clip.set_mask(mask)


def get_location_clip(
    garmin_segment: GarminSegment,
    video_length: timedelta,
    garmin_start_time: datetime,
    stats_refresh_period: timedelta,
    marker_size: int,
):
    fig_mpl = plt.figure(frameon=False, facecolor="black")
    ax = fig_mpl.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")

    verts = [
        (c.longitude, c.latitude)
        for c in garmin_segment.get_iterator(stats_refresh_period)
    ]

    (marker,) = ax.plot(
        [verts[0][0]],
        [verts[0][1]],
        marker="o",
        markersize=marker_size,
        markerfacecolor="white",
        markeredgecolor="white",
    )

    xs = [vert[0] for vert in verts]
    ys = [vert[1] for vert in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx, dy = max_x - min_x, max_y - min_y
    ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
    ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

    def make_frame_mpl(t):
        t = timedelta(seconds=t)
        coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

        marker.set_xdata([coordinate.longitude])
        marker.set_ydata([coordinate.latitude])

        frame = mplfig_to_npimage(fig_mpl)

        return frame

    def make_mask_mpl(t):
        t = timedelta(seconds=t)
        coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

        marker.set_xdata([coordinate.longitude])
        marker.set_ydata([coordinate.latitude])

        frame = make_frame_mpl(t.total_seconds())
        x, y, _ = frame.shape
        mask = (np.sum(frame, axis=2) > 10).reshape(x, y, 1)
        return mask

    mask = VideoClip(make_mask_mpl, duration=video_length.total_seconds(), ismask=True)
    clip = VideoClip(make_frame_mpl, duration=video_length.total_seconds())

    return clip.set_mask(mask)


def write_optimized_video(in_video_path: str, optimized_video_resolution: int) -> str:
    filename, ext = in_video_path.split(".")
    path = f"{filename}_{optimized_video_resolution}.{ext}"
    if os.path.isfile(path):
        print(f"Found pre-optimized video at path '{path}'")
        return path

    clip = VideoFileClip(in_video_path).resize(height=optimized_video_resolution)
    clip.write_videofile(path)
    return path
