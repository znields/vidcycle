# Vidcycle: Enhance Your Cycling Videos with GPS Data Overlay

Welcome to VidCycle, the innovative Python program designed for cycling enthusiasts and professionals alike. VidCycle transforms your cycling experiences by seamlessly integrating Garmin GPS bike computer data with your video footage. The tool overlays vital cycling metrics such as speed, elevation, distance, and heart rate onto your videos, creating an immersive and informative visual experience. 

With VidCycle, you can relive your rides with a modern, clean overlay that enriches your video content without overpowering it. Whether you're analyzing your performance, sharing your adventures with friends, or creating content for your audience, VidCycle offers a unique way to showcase your cycling journeys.

### Key Features:
- **GPS Data Integration**: Automatically syncs with Garmin GPS bike computer data.
- **Customizable Overlays**: Choose what data to display and how it appears on your video.
- **Modern Aesthetics**: Sleek, unobtrusive design that complements your footage.
- **Easy to Use**: User-friendly CLI tool for quick and effortless video enhancement.
- **Performance Insights**: Visualize your ride data for better performance analysis.

Get ready to elevate your cycling videos with VidCycle! 🚴💨

## Installation

1. Install `ffmpeg` and `python3` tools.
2. Clone the `vidcycle` repo.
3. Install the required Python packages by running `pip install -r requirements.txt`.
4. You're good to go!

## Usage

1. Begin recording a video on your camera of choice and make sure that the time on your camera is correctly set.
2. While the video is recording press the lap button on your Garmin bike computer.
3. Ensure that your camera microphone can hear the beep noise that plays from the Garmin computer so that you can specify this during rendering. The moment you press the lap button will be the "action" sync point to align your Garmin file and your video.
4. Finish your recording and bike ride and load the video files and the Garmin FIT file on to your computer.
5. Run `$ python3 main.py` specifying the parameters so that the program can align your video with the lap time that you marked on the Garmin computer. If you need help understanding the params, run `$ python3 main.py --help`.
6. Wait for the program to finish running and enjoy your video.

## Example Video

[![Fat Cake - Hawk Hill - August 22, 2023](https://img.youtube.com/vi/AgSG2Q-ejGk/0.jpg)](https://www.youtube.com/watch?v=AgSG2Q-ejGk)
