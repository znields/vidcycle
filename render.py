from datetime import timedelta, datetime
from coordinate import GarminSegment, GarminCoordinate, Speed
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
from matplotlib import font_manager


STATS_LABEL_FONT_SIZE = 70
STATS_FONT_SIZE = 200
STATS_FONT = font_manager.FontProperties(fname="fonts/Orbitron-Black.ttf")


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
        panel_width: float,
        map_height: float,
        map_opacity: float,
        map_marker_inner_size: int,
        map_marker_inner_opacity: float,
        map_marker_outer_size: int,
        map_marker_outer_opacity: float,
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
        self.panel_width = panel_width
        self.map_height = map_height
        self.map_opacity = map_opacity
        self.map_marker_inner_size = map_marker_inner_size
        self.map_marker_inner_opacity = map_marker_inner_opacity
        self.map_marker_outer_size = map_marker_outer_size
        self.map_marker_outer_opacity = map_marker_outer_opacity
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
        self.video_segment = self.segment.get_subsegment(
            self.segment_start_time,
            self.segment_start_time + self.video_length,
            timedelta(seconds=1 / self.video.get_fps()),
        )

        for thread, subsegment_coordinates in enumerate(
            np.array_split(self.video_segment.coordinates, self.num_threads)
        ):
            subsegments.append(
                (thread, self.video_segment, GarminSegment(subsegment_coordinates))
            )

        pool.Pool(self.num_threads).map(self.render_with_single_thread, subsegments)

    def render_with_single_thread(self, args):
        thread_number, video_segment, subsegment = args
        renderer = PanelRenderer(
            **{
                **self.__dict__,
                "segment": video_segment,
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
        panel_width: float,
        map_height: float,
        map_opacity: float,
        map_marker_inner_size: int,
        map_marker_inner_opacity: float,
        map_marker_outer_size: int,
        map_marker_outer_opacity: float,
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
        self.panel_width = panel_width
        self.map_height = map_height
        self.map_opacity = map_opacity
        self.map_marker_inner_size = map_marker_inner_size
        self.map_marker_inner_opacity = map_marker_inner_opacity
        self.map_marker_outer_size = map_marker_outer_size
        self.map_marker_outer_opacity = map_marker_outer_opacity
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
        path = Path(verts + [verts[-1]], codes + [Path.MOVETO])
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
        # TODO: move spacing to config file
        self.map_axis.set_xlim(min_x - (dx * 0.1), max_x + (dx * 0.1))
        self.map_axis.set_ylim(min_y - (dy * 0.1), max_y + (dy * 0.1))

    def plot_marker(self) -> None:
        start = self.segment.coordinates[0]
        (self.inner_marker,) = self.map_axis.plot(
            [start.longitude],
            [start.latitude],
            marker="o",
            markerfacecolor="white",
            markeredgecolor="white",
            markersize=self.map_marker_inner_size,
            alpha=self.map_marker_inner_opacity,
        )
        (self.outer_marker,) = self.map_axis.plot(
            [start.longitude],
            [start.latitude],
            marker="o",
            markerfacecolor="white",
            markeredgecolor="white",
            markersize=self.map_marker_outer_size,
            alpha=self.map_marker_outer_opacity,
        )

    def update_marker(self, coordinate: GarminCoordinate) -> None:
        for marker in [self.inner_marker, self.outer_marker]:
            marker.set_xdata([coordinate.longitude])
            marker.set_ydata([coordinate.latitude])

    def plot_stats(self) -> None:
        self.stats_axis = self.figure.add_axes([0, 0, 1, 1 - self.map_height])
        self.stats_axis.axis("off")
        num_stats = len(self.stat_keys_and_labels)
        y_positions = list(np.linspace(*self.stats_y_range, num_stats))
        self.key_to_stat_map: Dict[str, Tuple[Any, Any]] = {}
        start = self.segment.coordinates[0]
        for key_and_label, y_position in zip(self.stat_keys_and_labels, y_positions):
            key, label = key_and_label
            value = start.__dict__[key]

            value = self._make_value_text(value, label)

            stat_text = self.stats_axis.text(
                self.stats_x_position,
                y_position,
                value,
                color="white",
                fontsize=STATS_FONT_SIZE,
                fontproperties=STATS_FONT,
            )
            label_text = self.stats_axis.text(
                self.stats_x_position,
                y_position + self.stat_label_y_position_delta,
                label,
                color="white",
                fontsize=STATS_LABEL_FONT_SIZE,
                fontproperties=STATS_FONT,
            )
            stat_text.set_alpha(self.stats_opacity)
            label_text.set_alpha(self.stats_opacity)

            self.key_to_stat_map[key] = (stat_text, label_text)

    def update_stats(self, coordinate: GarminCoordinate) -> None:
        for key, stat_and_label in self.key_to_stat_map.items():
            stat, label = stat_and_label
            value = self._make_value_text(coordinate.__dict__[key], label.get_text())
            stat.set_text(value)

    def render(self) -> None:
        frame = 0
        for coordinate in self.subsegment.get_iterator(
            timedelta(seconds=(1 / self.video.get_fps()))
        ):
            self.update_marker(coordinate)
            self.update_stats(coordinate)
            self.figure.savefig(
                f"{self.output_folder}/{self.thread_number:04}{frame:08}",
                transparent=True,
            )
            frame += 1

    @staticmethod
    def _make_value_text(value: Any, label: str) -> str:
        if value is None:
            value = 0.0
        elif type(value) is Speed:
            if label.lower() == "mph":
                value = value.get_miles_per_hour()
            elif label.lower() == "mps":
                value = value.get_meters_per_second()
        return str(int(value))


class VideoRenderer(Renderer):
    def __init__(
        self,
        video: GoProVideo,
        video_length: timedelta,
        video_offset: timedelta,
        panel_folder: str,
        output_filepath: str,
        num_threads: int,
    ) -> None:
        self.video = video
        self.video_length = video_length
        self.video_offset = video_offset
        self.panel_folder = panel_folder
        self.output_filepath = output_filepath
        self.num_threads = num_threads

    def render(self) -> None:
        video_inputs = []
        audio_inputs = []
        for video_path in self.video.video_paths:
            input = ffmpeg.input(
                video_path,
            )
            video_inputs.append(input.video)
            audio_inputs.append(input.audio)

        start = self.video_offset.total_seconds()
        end = (self.video_length + self.video_offset).total_seconds()

        video_input = ffmpeg.concat(*video_inputs).trim(
            start=start,
            end=end,
        )
        audio_input = ffmpeg.concat(*audio_inputs, v=0, a=1).filter(
            "atrim", start=start, end=end
        )

        panel_overlay = ffmpeg.input(
            f"{self.panel_folder}/*.png",
            pattern_type="glob",
            framerate=self.video.get_fps(),
        )

        video_input = video_input.overlay(panel_overlay)
        audio_input = audio_input

        cmd = ffmpeg.output(
            video_input,
            audio_input,
            self.output_filepath,
            threads=self.num_threads,
            preset="ultrafast",
        )

        print(f"\nRunning command: ffmpeg {' '.join(cmd.get_args())}\n\n")

        cmd.run(overwrite_output=True)
