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

Welcome to the easy step-by-step installation process for VidCycle, Let's get you set up and ready to transform your rides into captivating stories.

#### Step 1: Get the Essentials
- **Install ffmpeg**: This is a powerful tool that VidCycle uses for video processing.
- **Install Python3**: Make sure you have Python3 on your system, as it's the heart of VidCycle.

#### Step 2: Get the VidCycle Code
- **Clone the VidCycle Repository**: Grab the latest version of VidCycle from our repository to ensure you have all the cool features.

#### Step 3: Install Python Packages
- **Run the Installation Command**: In your command line, type `pip install -r requirements.txt` to install all the necessary Python packages VidCycle needs to run smoothly.

#### Step 4: Ready, Set, Go!
- **You're All Set!**: Congratulations, you've successfully installed VidCycle! You're now ready to start adding awesome data overlays to your cycling videos.

## VidCycle Usage Guide

Here's a clear and simple guide to help you create those amazing videos with data overlays. Let's dive in!

#### Step 1: Start Your Journey
- **Record Your Ride**: Use any camera you like. Just make sure the time on your camera is correctly set to match real-world time.

#### Step 2: Mark Your Start Moments
- **Use the Lap Button**: While recording, press the lap button on your Garmin bike computer whenever you want to highlight a specific moment.
- **Catch the Beep**: Ensure your camera's microphone can pick up the beep from your Garmin. This beep is crucial as it serves as the 'action' sync point to align your Garmin data with your video.

#### Step 3: Save Your Adventure
- **Transfer Files to Your Computer**: After your ride, load both the video files and the Garmin FIT file onto your computer.

#### Step 4: Run VidCycle
- **Align and Process**: Execute `python3 main.py` with the necessary parameters to align your video with the lap times from your Garmin. Need help with parameters? Just run `python3 main.py --help` for guidance.

#### Step 5: Enjoy the Result
- **Relive Your Ride**: After the program finishes processing, sit back and enjoy your cycling journey with all the key data beautifully integrated into your video.

## Example Video

Here's an example video that gives you an idea of what you can create.

[![Fat Cake - Hawk Hill - August 22, 2023](https://img.youtube.com/vi/AgSG2Q-ejGk/0.jpg)](https://www.youtube.com/watch?v=AgSG2Q-ejGk)
