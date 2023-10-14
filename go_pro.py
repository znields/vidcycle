import subprocess
from typing import Tuple
from datetime import datetime, timezone, timedelta
import ffmpeg


def load_exif_data(video_file_path: str):
    output = subprocess.run(
        ["exiftool", "-api", "largefilesupport=1", video_file_path],
        capture_output=True,
    )
    out = output.stdout
    out = [[str(j).strip() for j in i.split(":", 1)] for i in str(out).split("\\n")]
    out = [i for i in out if len(i) == 2]
    return dict(out)


def get_start_and_end_time(video_file_path: str) -> Tuple[datetime, datetime]:
    exif_data = load_exif_data(video_file_path)
    video_start_time = datetime.strptime(
        exif_data["Track Create Date"], "%Y:%m:%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    track_duration = datetime.strptime(exif_data["Track Duration"], "%H:%M:%S")
    track_duration = timedelta(
        hours=track_duration.hour,
        minutes=track_duration.minute,
        seconds=track_duration.second,
    )
    return (
        video_start_time,
        video_start_time + track_duration,
    )


def get_video_resolution(video_file_path: str) -> Tuple[int, int]:
    probe = ffmpeg.probe(video_file_path)
    video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    video_stream = video_streams[0]
    return video_stream['width'], video_stream['height']
