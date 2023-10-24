import subprocess
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any
import ffmpeg
import functools


class Video:
    def __init__(self, video_path: str):
        self.video_path = video_path

    @functools.cache
    def get_duration(self) -> timedelta:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                self.video_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return timedelta(seconds=float(result.stdout))

    @functools.cache
    def get_resolution(self) -> Tuple[int, int]:
        probe = ffmpeg.probe(self.video_path)
        video_streams = [
            stream for stream in probe["streams"] if stream["codec_type"] == "video"
        ]
        video_stream = video_streams[0]
        return video_stream["width"], video_stream["height"]

    @functools.cache
    def get_fps(self):
        rate = str(
            subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "0",
                    "-of",
                    "compact=p=0",
                    "-select_streams",
                    "0",
                    "-show_entries",
                    "stream=r_frame_rate",
                    self.video_path,
                ],
                capture_output=True,
            ).stdout
        )

        numerator, denominator = rate[rate.index("=") + 1 : rate.index("|")].split("/")

        return int(numerator) / int(denominator)


class GoProVideo(Video):
    @functools.cache
    def load_exif_data(self) -> Dict[str, Any]:
        output = subprocess.run(
            ["exiftool", "-api", "largefilesupport=1", self.video_path],
            capture_output=True,
        )
        out = output.stdout
        out = [[str(j).strip() for j in i.split(":", 1)] for i in str(out).split("\\n")]
        out = [i for i in out if len(i) == 2]
        return dict(out)

    @functools.cache
    def get_start_time(self) -> datetime:
        exif_data = self.load_exif_data()
        video_start_time = datetime.strptime(
            exif_data["Track Create Date"], "%Y:%m:%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        return video_start_time

    @functools.cache
    def get_end_time(self) -> datetime:
        return self.get_start_time() + self.get_duration_from_exif()

    @functools.cache
    def get_duration_from_exif(self) -> timedelta:
        exif_data = self.load_exif_data()
        track_duration = datetime.strptime(exif_data["Track Duration"], "%H:%M:%S")
        return timedelta(
            hours=track_duration.hour,
            minutes=track_duration.minute,
            seconds=track_duration.second,
        )
