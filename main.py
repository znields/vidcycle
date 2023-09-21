import gpxpy
import gpxpy.gpx


gpx_file = open("gpx/Kill_Hawk_Hill.gpx", "r")
VIDEO_START = 1692683982

gpx = gpxpy.parse(gpx_file)


def get_coordinates_from_zero():
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


for coord in get_coordinates_from_zero():
    print(coord)
