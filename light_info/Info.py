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
        if lon < 0:
            lon = 360 + lon
        corners = [self.p1, self.p2, self.p3, self.p4]
        corners = utils.fix_antimeridian(corners)
        return geopoint_inside_polygon(
            (lon, lat),
            corners
        )

    @classmethod
    @abstractmethod
    def find_containing_point(
            cls,
            start: datetime.date,
            end: datetime.date,
            lon: float,
            lat: float,
    ) -> list[Info]:
        pass
