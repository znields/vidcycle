from datetime import timedelta, datetime
from coordinate import GarminSegment
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from typing import Optional
from typing import Any, Tuple, List
import os
from go_pro import get_video_resolution

STATS_X_POSITION = 0.15
POWER_Y_POSITION = 0.25
HEART_RATE_Y_POSITION = 0.45
CADENCE_Y_POSITION = 0.65
STAT_LABEL_Y_POSITION_DIFFERENCE = 0.11
STATS_LABEL_FONT_SIZE = 70
STATS_FONT_SIZE = 200

NUMBER_OF_THREADS = 63


class Renderer:
    pass


class ThreadedPanelRenderer(Renderer):
    def __init__(
        self,
        garmin_segment: GarminSegment,
        go_pro_video: GoProVideo,
        output_folder: str,
        frames_per_second: int,
        num_threads: int,
    ) -> None:
        self.garmin_segment = garmin_segment
        self.go_pro_video = go_pro_video
        self.output_folder = output_folder
        self.frames_per_second = frames_per_second
        self.num_threads = num_threads

    def render(self) -> None:
        pass

    def make_figure():
        pass


class PanelRenderer(Renderer):
    def __init__(
        self,
        garmin_segment: GarminSegment,
        go_pro_video: GoProVideo,
        output_folder: str,
        frames_per_second: int,
    ) -> None:
        self.garmin_segment = garmin_segment
        self.go_pro_video = go_pro_video
        self.output_folder = output_folder
        self.frames_per_second = frames_per_second

    def render(self) -> None:
        pass


class VideoRenderer(Renderer):
    def __init__(self, output_filepath: str) -> None:
        self.output_filepath = output_filepath


def write_video(
    in_video_path: str,
    out_video_path: Optional[str],
    garmin_segment: GarminSegment,
    garmin_start_time: datetime,
    video_length: timedelta,
    video_offset: timedelta,
    stats_refresh_period: timedelta,
) -> None:
    write_panel_as_images(in_video_path, garmin_segment, stats_refresh_period)


def write_panel_as_images(
    in_video_path: str,
    garmin_segment: GarminSegment,
    stats_refresh_period: timedelta,
    panel_width: float = 0.2,
    map_height: float = 0.3,
    map_opacity: float = 0.9,
    marker_size: int = 15,
):
    coordinates = [c for c in garmin_segment.get_iterator(stats_refresh_period)]
    verts = [(c.longitude, c.latitude) for c in coordinates]
    xs = [vert.longitude for vert in coordinates]
    ys = [vert.latitude for vert in coordinates]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx, dy = max_x - min_x, max_y - min_y
    width, height = get_video_resolution(in_video_path)

    fig_mpl = plt.figure(
        frameon=False,
        dpi=100,
        figsize=(
            (width / 100) * panel_width,
            (height / 100),
        ),
    )

    def plot_map_and_marker():
        ax = fig_mpl.add_axes([0, 1 - map_height, 1, map_height])
        ax.axis("off")

        codes = [Path.MOVETO] + [Path.CURVE3 for _ in range(len(verts) - 1)]
        path = Path(verts, codes)
        patch = patches.PathPatch(
            path,
            edgecolor=(1, 1, 1, map_opacity),
            facecolor="none",
            lw=6,
        )
        ax.add_patch(patch)

        ax.plot(
            [verts[0][0]],
            [verts[0][1]],
            marker="o",
            markersize=marker_size,
            markerfacecolor="white",
            markeredgecolor="white",
        )
        ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
        ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

    def plot_stats():
        ax = fig_mpl.add_axes([0, 0, 1, 1 - map_height])
        ax.axis("off")

        texts = [
            ax.text(
                STATS_X_POSITION,
                POWER_Y_POSITION,
                str(int(coordinates[400].power)),
                fontsize=STATS_FONT_SIZE,
                color="white",
            ),
            ax.text(
                STATS_X_POSITION,
                POWER_Y_POSITION + STAT_LABEL_Y_POSITION_DIFFERENCE,
                "PWR",
                fontsize=STATS_LABEL_FONT_SIZE,
                color="white",
            ),
            ax.text(
                STATS_X_POSITION,
                HEART_RATE_Y_POSITION,
                str(int(coordinates[400].heart_rate)),
                fontsize=STATS_FONT_SIZE,
                color="white",
            ),
            ax.text(
                STATS_X_POSITION,
                HEART_RATE_Y_POSITION + STAT_LABEL_Y_POSITION_DIFFERENCE,
                "HR",
                fontsize=STATS_LABEL_FONT_SIZE,
                color="white",
            ),
            ax.text(
                STATS_X_POSITION,
                CADENCE_Y_POSITION,
                str(int(coordinates[400].cadence)),
                fontsize=STATS_FONT_SIZE,
                color="white",
            ),
            ax.text(
                STATS_X_POSITION,
                CADENCE_Y_POSITION + STAT_LABEL_Y_POSITION_DIFFERENCE,
                "RPM",
                fontsize=STATS_LABEL_FONT_SIZE,
                color="white",
            ),
        ]
        for text in texts:
            text.set_alpha(map_opacity)

    plot_map_and_marker()
    plot_stats()
    fig_mpl.savefig("panel/000400.png", transparent=True)

    # def get_map_clips(
    #     garmin_segment: GarminSegment,
    #     garmin_start_time: datetime,
    #     video_length: timedelta,
    #     stats_refresh_period: timedelta,
    #     inner_marker_size: int,
    #     outer_marker_size: int,
    # ) -> Tuple[ImageClip, VideoClip, VideoClip]:
    #     def get_segment_clip():
    #         frame = mplfig_to_npimage(fig_mpl)
    #         x, y, _ = frame.shape
    #         mask = (np.sum(frame, axis=2) > 10).reshape(x, y)

    #         mask = ImageClip(mask, duration=video_length.total_seconds(), ismask=True)
    #         clip = ImageClip(frame, duration=video_length.total_seconds())

    #         return clip.set_mask(mask)

    # def get_location_marker_clip(marker_size: int):
    #     fig_mpl = plt.figure(frameon=False, facecolor="black")
    #     ax = fig_mpl.add_axes([0, 0, 1, 1])
    #     ax.set_facecolor("black")

    #     (marker,) = ax.plot(
    #         [verts[0][0]],
    #         [verts[0][1]],
    #         marker="o",
    #         markersize=marker_size,
    #         markerfacecolor="white",
    #         markeredgecolor="white",
    #     )


#         ax.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
#         ax.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

#         def make_frame_mpl(t):
#             t = timedelta(seconds=t)
#             coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

#             marker.set_xdata([coordinate.longitude])
#             marker.set_ydata([coordinate.latitude])

#             return mplfig_to_npimage(fig_mpl)

#         def make_mask_mpl(t):
#             t = timedelta(seconds=t)
#             coordinate = garmin_segment.get_coordinate(garmin_start_time + t)

#             marker.set_xdata([coordinate.longitude])
#             marker.set_ydata([coordinate.latitude])

#             frame = make_frame_mpl(t.total_seconds())
#             x, y, _ = frame.shape
#             mask = (np.sum(frame, axis=2) > 10).reshape(x, y, 1)
#             return mask

#         mask = VideoClip(
#             make_mask_mpl, duration=video_length.total_seconds(), ismask=True
#         )
#         clip = VideoClip(make_frame_mpl, duration=video_length.total_seconds())

#         return clip.set_mask(mask)

#     return (
#         get_segment_clip(),
#         get_location_marker_clip(inner_marker_size),
#         get_location_marker_clip(outer_marker_size),
#     )


# def write_optimized_video(in_video_path: str, optimized_video_resolution: int) -> str:
#     filename, ext = in_video_path.split(".")
#     path = f"{filename}_{optimized_video_resolution}.{ext}"
#     if os.path.isfile(path):
#         print(f"Found pre-optimized video at path '{path}'")
#         return path

#     clip = VideoFileClip(in_video_path).resize(height=optimized_video_resolution)
#     clip.write_videofile(path, threads=64)
#     return path
