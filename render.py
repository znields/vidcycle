from moviepy import *
from moviepy.editor import *
from datetime import timedelta, datetime
from coordinate import Segment
import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from typing import Optional
from typing import Any


def write_video(
    in_video_path: str,
    out_video_path: Optional[str],
    render_height: int,
    video_segment: Segment,
    video_start_time: datetime,
    video_end_time: datetime,
    video_length: timedelta,
    video_offset: timedelta,
    stats_refresh_period: timedelta,
) -> None:
    clip = (
        VideoFileClip(in_video_path)
        # .resize(height=render_height)
        .subclip(
            video_offset.total_seconds(),
            video_offset.total_seconds() + video_length.total_seconds(),
        )
    )
    video_subsegment = video_segment.get_subsegment(
        video_start_time, video_end_time, stats_refresh_period
    )
    stat_clips = get_stat_clips(
        video_subsegment,
        video_length,
        stats_refresh_period,
    )

    map_clip = (
        get_map_clip(
            video_segment,
            video_length,
            video_start_time,
            stats_refresh_period,
            render_height,
        )
        .set_opacity(0.9)
        .set_position((0.01, 0.01), relative=True)
        .resize(0.75)
    )

    location_clip_inner = (
        get_location_clip(
            video_segment,
            video_length,
            video_start_time,
            stats_refresh_period,
            render_height,
            15,
        )
        .set_opacity(1.0)
        .set_position((0.01, 0.01), relative=True)
        .resize(0.75)
    )

    location_clip_outer = (
        get_location_clip(
            video_segment,
            video_length,
            video_start_time,
            stats_refresh_period,
            render_height,
            25,
        )
        .set_opacity(0.3)
        .set_position((0.01, 0.01), relative=True)
        .resize(0.75)
    )

    video = CompositeVideoClip(
        [clip, map_clip, location_clip_inner, location_clip_outer] + stat_clips
    )

    if out_video_path is None:
        video.without_audio().preview(fps=30)
    else:
        video.write_videofile(out_video_path, fps=2)


def get_stat_clips(
    video_segment: Segment, video_length: timedelta, stats_refresh_period: timedelta
):
    def data_to_str(data: Any):
        if data is None:
            return "0"

        if type(data) == float:
            return str(int(data))

        return str(data)

    def get_font_size(key: str) -> int:
        if key == "timestamp":
            return 70

        return 120

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
        for coordinate in video_segment.get_iterator(stats_refresh_period):
            text_clip = (
                TextClip(
                    data_to_str(coordinate.__dict__[key])
                    + ("" if label is None else "\n" + label),
                    fontsize=get_font_size(key),
                    color="white",
                    font="Helvetica-Bold",
                )
                .set_duration(stats_refresh_period.total_seconds())
                .set_opacity(0.75)
            )
            text_clips.append(text_clip)

        stat_clip = (
            concatenate_videoclips(text_clips)
            .set_position((0.01, idx / 10), relative=True)
            .subclip(0, video_length.total_seconds())
        )

        stat_clips.append(stat_clip)
    return stat_clips


def get_map_clip(
    video_segment: Segment,
    video_length: timedelta,
    video_start_time: datetime,
    stats_refresh_period: timedelta,
    render_height: int,
):
    fig_mpl = plt.figure(frameon=False, facecolor="black")
    ax = fig_mpl.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")

    verts = [
        (c.longitude, c.latitude)
        for c in video_segment.get_iterator(stats_refresh_period)
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
    video_segment: Segment,
    video_length: timedelta,
    video_start_time: datetime,
    stats_refresh_period: timedelta,
    render_height: int,
    marker_size: int,
):
    fig_mpl = plt.figure(frameon=False, facecolor="black")
    ax = fig_mpl.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")

    verts = [
        (c.longitude, c.latitude)
        for c in video_segment.get_iterator(stats_refresh_period)
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
        coordinate = video_segment.get_coordinate(video_start_time + t)

        marker.set_xdata([coordinate.longitude])
        marker.set_ydata([coordinate.latitude])

        frame = mplfig_to_npimage(fig_mpl)

        return frame

    def make_mask_mpl(t):
        t = timedelta(seconds=t)
        coordinate = video_segment.get_coordinate(video_start_time + t)

        marker.set_xdata([coordinate.longitude])
        marker.set_ydata([coordinate.latitude])

        frame = make_frame_mpl(t.total_seconds())
        x, y, _ = frame.shape
        mask = (np.sum(frame, axis=2) > 10).reshape(x, y, 1)
        return mask

    mask = VideoClip(make_mask_mpl, duration=video_length.total_seconds(), ismask=True)
    clip = VideoClip(make_frame_mpl, duration=video_length.total_seconds())

    return clip.set_mask(mask)
