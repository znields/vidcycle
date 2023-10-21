from datetime import timedelta, datetime
from coordinate import GarminSegment, GarminCoordinate
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from matplotlib.path import Path
from typing import Any, Tuple, List, Dict
from video import GoProVideo
from multiprocessing import pool
import os
import shutil
import ffmpeg

STATS_LABEL_FONT_SIZE = 70
STATS_FONT_SIZE = 200


class Renderer:
    pass


class ThreadedPanelRenderer(Renderer):
    def __init__(
        self,
        segment: GarminSegment,
        segment_start_time: datetime,
        video_length: timedelta,
        video: GoProVideo,
        output_folder: str,
        frames_per_second: int,
        panel_width: float,
        map_height: float,
        map_opacity: float,
        map_marker_size: int,
        stat_keys_and_labels: List[Tuple[str, str]],
        stats_x_position: float,
        stats_y_range: Tuple[float, float],
        stat_label_y_position_delta: float,
        stats_opacity: float,
        num_threads: int,
    ) -> None:
        self.segment = segment
        self.segment_start_time = segment_start_time
        self.video_length = video_length
        self.video = video
        self.output_folder = output_folder
        self.frames_per_second = frames_per_second
        self.panel_width = panel_width
        self.map_height = map_height
        self.map_opacity = map_opacity
        self.map_marker_size = map_marker_size
        self.stat_keys_and_labels = stat_keys_and_labels
        self.stats_x_position = stats_x_position
        self.stats_y_range = stats_y_range
        self.stat_label_y_position_delta = stat_label_y_position_delta
        self.stats_opacity = stats_opacity
        self.num_threads = num_threads

    def clean_output_folder(self) -> None:
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)
        os.makedirs(self.output_folder, exist_ok=True)

    def render(self) -> None:
        self.clean_output_folder()
        subsegments = []
        for thread in range(self.num_threads):
            subsegment = self.get_subsegment_for_thread(thread)
            subsegments.append((thread, subsegment))

        pool.Pool(self.num_threads).map(self.render_with_single_thread, subsegments)

    def get_subsegment_for_thread(self, thread: int) -> GarminSegment:
        subsegment_length = self.video_length / self.num_threads
        start_time = self.segment_start_time + (subsegment_length * thread)
        end_time = start_time + subsegment_length
        return self.segment.get_subsegment(
            start_time, end_time, timedelta(seconds=1 / self.frames_per_second)
        )

    def render_with_single_thread(self, args):
        thread_number, subsegment = args
        renderer = PanelRenderer(
            **{
                **self.__dict__,
                "segment": self.segment,
                "subsegment": subsegment,
                "thread_number": thread_number,
            },
        )
        renderer.render()


class PanelRenderer(Renderer):
    def __init__(
        self,
        segment: GarminSegment,
        subsegment: GarminSegment,
        video: GoProVideo,
        output_folder: str,
        thread_number: int,
        frames_per_second: int,
        panel_width: float,
        map_height: float,
        map_opacity: float,
        map_marker_size: int,
        stat_keys_and_labels: List[Tuple[str, str]],
        stats_x_position: float,
        stats_y_range: Tuple[float, float],
        stat_label_y_position_delta: float,
        stats_opacity: float,
        **_,
    ) -> None:
        self.segment = segment
        self.subsegment = subsegment
        self.video = video
        self.output_folder = output_folder
        self.thread_number = thread_number
        self.frames_per_second = frames_per_second
        self.panel_width = panel_width
        self.map_height = map_height
        self.map_opacity = map_opacity
        self.map_marker_size = map_marker_size
        self.stat_keys_and_labels = stat_keys_and_labels
        self.stats_x_position = stats_x_position
        self.stats_y_range = stats_y_range
        self.stat_label_y_position_delta = stat_label_y_position_delta
        self.stats_opacity = stats_opacity
        self.make_figure()

        # for now, let's keep the map static
        # and only render it once
        self.plot_map()
        self.plot_marker()
        self.plot_stats()

    def make_figure(self) -> None:
        width, height = self.video.get_resolution()
        figure = plt.figure(
            frameon=False,
            dpi=100,
            figsize=(
                (width / 100) * self.panel_width,
                (height / 100),
            ),
        )
        self.figure = figure

    def plot_map(self) -> None:
        self.map_axis = self.figure.add_axes(
            [0, 1 - self.map_height, 1, self.map_height]
        )
        self.map_axis.axis("off")

        verts = [(c.longitude, c.latitude) for c in self.segment.coordinates]
        codes = [Path.MOVETO] + [Path.CURVE3 for _ in range(len(verts) - 1)]
        path = Path(verts, codes)
        patch = patches.PathPatch(
            path,
            edgecolor=(1, 1, 1, self.map_opacity),
            facecolor="none",
            lw=6,
        )

        xs = [vert[0] for vert in verts]
        ys = [vert[1] for vert in verts]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        dx, dy = max_x - min_x, max_y - min_y

        self.map_axis.add_patch(patch)
        self.map_axis.set_xlim(min_x - (dx * 0.01), max_x + (dx * 0.01))
        self.map_axis.set_ylim(min_y - (dy * 0.01), max_y + (dy * 0.01))

    def plot_marker(self) -> None:
        start = self.segment.coordinates[0]
        (self.marker,) = self.map_axis.plot(
            [start.longitude],
            [start.latitude],
            marker="o",
            markersize=self.map_marker_size,
            markerfacecolor="white",
            markeredgecolor="white",
        )

    def update_marker(self, coordinate: GarminCoordinate) -> None:
        self.marker.set_xdata([coordinate.longitude])
        self.marker.set_ydata([coordinate.latitude])

    def plot_stats(self) -> None:
        self.stats_axis = self.figure.add_axes([0, 0, 1, 1 - self.map_height])
        num_stats = len(self.stat_keys_and_labels)
        y_positions = list(np.linspace(*self.stats_y_range, num_stats))
        self.key_to_stat_map: Dict[str, Any] = {}
        start = self.segment.coordinates[0]
        for key_and_label, y_position in zip(self.stat_keys_and_labels, y_positions):
            key, label = key_and_label
            value = start.__dict__[key]
            stat_text = self.stats_axis.text(
                self.stats_x_position,
                y_position,
                "0" if value is None else str(int(value)),
                color="white",
                fontsize=STATS_FONT_SIZE,
            )
            label_text = self.stats_axis.text(
                self.stats_x_position,
                y_position + self.stat_label_y_position_delta,
                label,
                color="white",
                fontsize=STATS_LABEL_FONT_SIZE,
            )
            stat_text.set_alpha(self.stats_opacity)
            label_text.set_alpha(self.stats_opacity)

            self.key_to_stat_map[key] = stat_text

    def update_stats(self, coordinate: GarminCoordinate) -> None:
        for key, stat in self.key_to_stat_map.items():
            value = coordinate.__dict__[key]
            stat.set_text("0" if value is None else str(int(value)))

    def render(self) -> None:
        frame = 0
        for coordinate in self.subsegment.get_iterator(
            timedelta(seconds=(1 / self.frames_per_second))
        ):
            self.update_marker(coordinate)
            self.update_stats(coordinate)
            self.figure.savefig(
                f"{self.output_folder}/{self.thread_number}{frame:08}", transparent=True
            )
            frame += 1


class VideoRenderer(Renderer):
    def __init__(
        self,
        video: GoProVideo,
        panel_folder: str,
        output_filepath: str,
    ) -> None:
        self.video = video
        self.panel_folder = panel_folder
        self.output_filepath = output_filepath

    def render(self) -> None:
        video = ffmpeg.input(self.video.video_path)
        panel_overlay = ffmpeg.input(
            f"{self.panel_folder}/*.png", pattern_type="glob", framerate=30
        )

        video.overlay(panel_overlay).output(self.output_filepath).run()
