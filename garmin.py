from garmin_fit_sdk import Decoder, Stream
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from coordinate import Coordinate


class GarminCoordinate(Coordinate):
    def __init__(
        self,
        timestamp: datetime,
        distance: float,
        altitude: float,
        temperature: int,
        heart_rate: Optional[int] = None,
        speed: Optional[float] = None,
        position_lat: Optional[int] = None,
        position_long: Optional[int] = None,
        power: Optional[int] = None,
        cadence: Optional[int] = None,
        **_kwargs: Dict[str, Any]
    ):
        if position_lat is not None:
            position_lat /= 11930465
        if position_long is not None:
            position_long /= 11930465

        super().__init__(timestamp, position_lat, position_long)

        self.distance = distance
        self.altitude = altitude
        self.speed = speed
        self.heart_rate = heart_rate
        self.temperature = temperature
        self.power = power
        self.cadence = cadence

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=4, default=str)


def load_coordinates_from_file(path: str) -> List[GarminCoordinate]:
    stream = Stream.from_file(path)

    decoder = Decoder(stream)
    messages, _ = decoder.read()

    coordinates = []
    for message in messages["record_mesgs"]:
        message = {key: message[key] for key in message if type(key) == str}
        coordinates.append(GarminCoordinate(**message))
    return coordinates
