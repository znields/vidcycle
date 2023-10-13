from datetime import timedelta, datetime
from coordinate import GarminSegment
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from typing import Optional
from typing import Any, Tuple, List
import os

FRAMES_PER_SECOND = 30
STAT_FONT_SIZE = 350
LABEL_FONT_SIZE = 100
STAT_CLIP_X_POS = 0.02


def write_video(
    original_in_video_path: str,
    in_video_path: str,
    out_video_path: Optional[str],
    optimized_video_resolution: Optional[int],
    garmin_segment: GarminSegment,
    garmin_start_time: datetime,
    video_length: Optional[timedelta],
    video_offset: timedelta,
    stats_refresh_period: timedelta,
) -> None:
    pass


def get_map_clips(
    garmin_segment: GarminSegment,
    garmin_start_time: datetime,
    video_length: timedelta,
    stats_refresh_period: timedelta,
    inner_marker_size: int,
    outer_marker_size: int,
) -> Tuple[ImageClip, VideoClip, VideoClip]:
    verts = [
        (c.longitude, c.latitude)
        for c in garmin_segment.get_iterator(stats_refresh_period)
    ]
    xs = [vert[0] for vert in verts]
    ys = [vert[1] for vert in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx, dy = max_x - min_x, max_y - min_y

    def get_segment_clip():
        fig_mpl = plt.figure(frameon=False, facecolor="black")
        ax = fig_mpl.add_axes([0, 0, 1, 1])
        ax.set_facecolor("black")

        codes = [Path.MOVETO] + [Path.CURVE3 for _ in range(len(verts) - 1)]
        path = Path(verts, codes)
        patch = patches.PathPatch(path, edgecolor="white", facecolor="none", lw=6)
        ax.add_patch(patch)

        ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
        ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

        frame = mplfig_to_npimage(fig_mpl)
        x, y, _ = frame.shape
        mask = (np.sum(frame, axis=2) > 10).reshape(x, y)

        mask = ImageClip(mask, duration=video_length.total_seconds(), ismask=True)
        clip = ImageClip(frame, duration=video_length.total_seconds())

        return clip.set_mask(mask)

    def get_location_marker_clip(marker_size: int):
        fig_mpl = plt.figure(frameon=False, facecolor="black")
        ax = fig_mpl.add_axes([0, 0, 1, 1])
        ax.set_facecolor("black")

        (marker,) = ax.plot(
            [verts[0][0]],
            [verts[0][1]],
            marker="o",
            markersize=marker_size,
            markerfacecolor="white",
            markeredgecolor="white",
        )

        ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
        ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

        def make_frame_mpl(t):
            t = timedelta(seconds=t)
            coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

            marker.set_xdata([coordinate.longitude])
            marker.set_ydata([coordinate.latitude])

            return mplfig_to_npimage(fig_mpl)

        def make_mask_mpl(t):
            t = timedelta(seconds=t)
            coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

            marker.set_xdata([coordinate.longitude])
            marker.set_ydata([coordinate.latitude])

            frame = make_frame_mpl(t.total_seconds())
            x, y, _ = frame.shape
            mask = (np.sum(frame, axis=2) > 10).reshape(x, y, 1)
            return mask

        mask = VideoClip(
            make_mask_mpl, duration=video_length.total_seconds(), ismask=True
        )
        clip = VideoClip(make_frame_mpl, duration=video_length.total_seconds())

        return clip.set_mask(mask)

    return (
        get_segment_clip(),
        get_location_marker_clip(inner_marker_size),
        get_location_marker_clip(outer_marker_size),
    )


def write_optimized_video(in_video_path: str, optimized_video_resolution: int) -> str:
    filename, ext = in_video_path.split(".")
    path = f"{filename}_{optimized_video_resolution}.{ext}"
    if os.path.isfile(path):
        print(f"Found pre-optimized video at path '{path}'")
        return path

    clip = VideoFileClip(in_video_path).resize(height=optimized_video_resolution)
    clip.write_videofile(path, threads=64)
    return path
