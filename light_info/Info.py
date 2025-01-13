from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

import utils
from custom_types import LonLat
from utils import geopoint_inside_polygon


@dataclass
class Info(ABC):
    # corner points coords (lon, lat)
    p1: LonLat
    p2: LonLat
    p3: LonLat
    p4: LonLat

    dt: datetime.datetime
    satellite: str

    filename: str

    def contains_pos(self, lon: float, lat: float) -> bool:
        # if lon < 0:
        #     lon = 360 + lon
        corners = [self.p1, self.p2, self.p3, self.p4]
        corners = utils.fix_antimeridian(corners)
        return geopoint_inside_polygon(
            (lon, lat),
            corners
        )

    def center_coord(self) -> LonLat:
        lon = (self.p1[0] + self.p2[0] + self.p3[0] + self.p4[0]) / 4
        lat = (self.p1[1] + self.p2[1] + self.p3[1] + self.p4[1]) / 4
        return lon, lat

    @staticmethod
    @abstractmethod
    def find(
            start: datetime.date,
            end: datetime.date,
            point: LonLat = None
    ) -> list[Info]:
        pass