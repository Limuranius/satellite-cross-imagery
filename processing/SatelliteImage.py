from abc import ABC
from datetime import datetime

import folium
import numpy as np
from scipy.spatial import KDTree

import utils
from custom_types import LonLat


class SatelliteImage(ABC):
    file_path: str
    satellite_name: str

    latitude: np.ndarray
    longitude: np.ndarray
    radiance: np.ndarray
    reflectance: np.ndarray
    sensor_zenith: np.ndarray
    solar_zenith: np.ndarray

    dt: datetime

    band: str
    wavelength: int

    geo_kdtree: KDTree

    def create_kdtree(self):
        coords = np.array([self.longitude, self.latitude])
        coords = coords.transpose((1, 2, 0))
        coords = coords.reshape((-1, 2))  # flatten
        self.geo_kdtree = KDTree(coords)

    def get_corners_coords(self) -> tuple[LonLat, LonLat, LonLat, LonLat]:
        # Returns geo-coordinates of corners of image (longitude, latitude)
        tl = (self.longitude[0, 0], self.latitude[0, 0])
        tr = (self.longitude[0, -1], self.latitude[0, -1])
        br = (self.longitude[-1, -1], self.latitude[-1, -1])
        bl = (self.longitude[-1, 0], self.latitude[-1, 0])
        return tl, tr, br, bl

    def get_closest_pixel(self, lon: float, lat: float) -> tuple[int, int]:
        coords = np.stack([self.longitude, self.latitude]).transpose((1, 2, 0))
        dist = np.linalg.norm(coords - [lon, lat], axis=2)
        i, j = np.unravel_index(dist.argmin(), self.latitude.shape)
        return i, j

    def contains_pos(self, lon: float, lat: float) -> bool:
        corners = self.get_corners_coords()
        return utils.geopoint_inside_polygon(
            (lon, lat),
            corners
        )

    def show_on_map(self, map_obj: folium.Map):
        corners = self.get_corners_coords()
        folium.Polygon(
            utils.reverse_coords(utils.fix_antimeridian(corners)),
        ).add_to(map_obj)
