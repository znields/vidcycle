# Vidcycle

## Installation

1. Clone the `vidcycle` repo.
2. Install `ffmpeg` and `python3` applications.
3. Install the required Python packages by running `pip install -r requirements.txt`.
4. You're good to go!

### Usage

To begin rendering your first video, you will work with the `main.py` file. See below for this scripts documentation:

```
% python3 main.py --help 
usage: main.py [-h] --fit-file FIT_FILE --video-files [VIDEO_FILES ...] [--video-length-in-secs VIDEO_LENGTH_IN_SECS]
               [--video-offset-start-in-secs VIDEO_OFFSET_START_IN_SECS] --video-output-path VIDEO_OUTPUT_PATH --video-lap-time-in-secs
               VIDEO_LAP_TIME_IN_SECS --lap-time-search-window-in-secs LAP_TIME_SEARCH_WINDOW_IN_SECS LAP_TIME_SEARCH_WINDOW_IN_SECS
               --render-config-file RENDER_CONFIG_FILE

Program to add metadata to cycling video from GoPro

optional arguments:
  -h, --help            show this help message and exit
  --fit-file FIT_FILE   FIT file of ride
  --video-files [VIDEO_FILES ...]
                        Video files of ride
  --video-length-in-secs VIDEO_LENGTH_IN_SECS
                        How many seconds the video should last
  --video-offset-start-in-secs VIDEO_OFFSET_START_IN_SECS
                        How many seconds into the video should the output start
  --video-output-path VIDEO_OUTPUT_PATH
                        Video output path. If none then will preview video.
  --video-lap-time-in-secs VIDEO_LAP_TIME_IN_SECS
                        Lap time in seconds from the video.
  --lap-time-search-window-in-secs LAP_TIME_SEARCH_WINDOW_IN_SECS LAP_TIME_SEARCH_WINDOW_IN_SECS
                        Search window for lap time.
  --render-config-file RENDER_CONFIG_FILE
                        Render config file to determine video render style
```