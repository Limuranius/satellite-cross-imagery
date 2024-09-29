import random

from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, Polygon, Feature


def geopoint_inside_polygon(
        point: tuple[float, float],
        polygon: list[tuple[float, float]]
) -> bool:
    point = Feature(geometry=Point(point))
    polygon = Polygon([polygon])
    return boolean_point_in_polygon(point, polygon)


def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


def reverse_coords(coords_list):
    result = []
    for coord in coords_list:
        result.append(list(reversed(coord)))
    return result


def fix_antimeridian(coords_list):
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
