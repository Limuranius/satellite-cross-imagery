import random
from datetime import datetime, timedelta

import shapely
from geojson import Point, Polygon, Feature
from turfpy.measurement import boolean_point_in_polygon

from custom_types import LonLat, LatLon


def geopoint_inside_polygon(
        point: LonLat,
        polygon: list[LonLat]
) -> bool:
    point = Feature(geometry=Point(point))
    polygon = Polygon([polygon])
    return boolean_point_in_polygon(point, polygon)


def random_color() -> str:
    return "#%06x" % random.randint(0, 0xFFFFFF)


def reverse_coords(coords_list: list[LonLat]) -> list[LatLon]:
    result = []
    for coord in coords_list:
        result.append(list(reversed(coord)))
    return result


def fix_antimeridian(coords_list: list[LonLat]) -> list[LonLat]:
    lons = [coord[0] for coord in coords_list]
    need_fixing = any([lon > 100 for lon in lons]) and any([lon < -100 for lon in lons])
    if not need_fixing:
        return coords_list
    result = []
    for lon, lat in coords_list:
        if lon < 0:
            lon = 360 + lon
        result.append((lon, lat))
    return result


def intersection_percent(
        poly1: list[LonLat],
        poly2: list[LonLat],
) -> float:
    poly1 = shapely.Polygon(shell=poly1)
    poly2 = shapely.Polygon(shell=poly2)
    inter = poly1.intersection(poly2)
    return inter.area / (poly1.area + poly2.area - inter.area)


def datetime_range(start: datetime, end: datetime, step: timedelta = timedelta(minutes=5)):
    curr = start
    while curr <= end:
        yield curr
        curr += step
