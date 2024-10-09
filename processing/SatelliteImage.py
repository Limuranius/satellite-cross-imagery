from abc import ABC, abstractmethod
from datetime import datetime

import numpy as np

import satpy

from custom_types import LonLat
from utils import geopoint_inside_polygon


class SatelliteImage(ABC):
    file_path: str

    latitude: np.ndarray
    longitude: np.ndarray
    radiance: np.ndarray
    sensor_zenith: np.ndarray

    dt: datetime

    band: str
    wavelength: int

    def get_corners_coords(self) -> tuple[LonLat, LonLat, LonLat, LonLat]:
        # Returns geo-coordinates of corners of image (longitude, latitude)
        tl = (self.longitude[0, 0], self.latitude[0, 0])
        tr = (self.longitude[0, -1], self.latitude[0, -1])
        br = (self.longitude[-1, -1], self.latitude[-1, -1])
        bl = (self.longitude[-1, 0], self.latitude[-1, 0])
        return tl, tr, br, bl

    def get_closest_pixel(self, lon: float, lat: float) -> tuple[int, int]:
        # Returns raster coordinates of pixel closest to (lat, lon)
        distance = (
                np.abs(self.latitude - lat) ** 2
                + np.abs(self.longitude - lon) ** 2
        )
        i, j = np.unravel_index(distance.argmin(), distance.shape)
        return i, j

    def contains_pos(self, lon: float, lat: float) -> bool:
        corners = self.get_corners_coords()
        return geopoint_inside_polygon(
            (lon, lat),
            corners
        )
