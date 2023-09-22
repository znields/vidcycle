import gpxpy
import gpxpy.gpx
import argparse

parser = argparse.ArgumentParser(
    description="Program to add metadata to cycling video from GoPro"
)
parser.add_argument("--gpx-file", help="GPX file of ride", required=True)
parser.add_argument("--video-file", help="Video file of ride", required=True)
args = vars(parser.parse_args())


def load_gpx_file():
    gpx_file = open(args["gpx_file"], "r")
    gpx = gpxpy.parse(gpx_file)
    return gpx


def get_data_from_gpx(gpx):
    coordinates = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append(
                    {
                        "time": point.time.timestamp(),
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "elevation": point.elevation,
                        "point": point,
                    }
                )
    coordinates = add_speed_to_coordinates(coordinates)
    coordinates = add_extension_data_to_coordinates(coordinates)
    return coordinates


def add_speed_to_coordinates(coordinates):
    first = coordinates[0]
    coordinates_with_speed = []
    for coordinate in coordinates:
        coordinates_with_speed.append(
            {
                "latitude": coordinate["latitude"] - first["latitude"],
                "longitude": coordinate["longitude"] - first["longitude"],
                "speed": 0.0
                if len(coordinates_with_speed) == 0
                else coordinate["point"].speed_between(
                    coordinates_with_speed[-1]["point"]
                ),
                **coordinate,
            }
        )
    return coordinates_with_speed


def add_extension_data_to_coordinates(coordinates):
    coordinates_with_metadata = []
    for coordinate in coordinates:
        extensions = coordinate["point"].extensions
        if len(extensions) == 1:
            power = 0
            temp, hr, cad = [int(ext.text) for ext in extensions[0]]
        else:
            power, other = extensions
            temp, hr, cad = [int(ext.text) for ext in other]
            power = int(power.text)

        coordinate = {**coordinate, "power": power, "temp": temp, "hr": hr, "cad": cad}
        del coordinate["point"]
        coordinates_with_metadata.append(coordinate)
    return coordinates_with_metadata


if __name__ == "__main__":
    gpx = load_gpx_file()
    for datum in get_data_from_gpx(gpx):
        print(datum)
