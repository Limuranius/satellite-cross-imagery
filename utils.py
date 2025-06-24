import pathlib
import random
from datetime import datetime, timedelta

import cv2
import numpy as np
import shapely
import statsmodels.api as sm
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


def iou(
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


def match_dts_timedelta(
        dts1: list[datetime],
        dts2: list[datetime],
        td: timedelta,
) -> dict[datetime, list[datetime]]:
    groups = dict()
    for dt1 in dts1:
        group = []
        for dt2 in dts2:
            if abs(dt1 - dt2) <= td:
                group.append(dt2)
        if len(group) > 0:
            groups[dt1] = group
    return groups


def get_image_gradient(img: np.ndarray) -> np.ndarray:
    dx_k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    dy_k = dx_k.T
    dx = cv2.filter2D(img, -1, dx_k)
    dy = cv2.filter2D(img, -1, dy_k)
    return np.hypot(dx, dy)


def linregress_report(
        x,
        y,
        use_intercept=False,
        round_slope=2,
        round_intercept=2,
):
    if use_intercept:
        x = sm.add_constant(x)
    model = sm.OLS(y, x)
    results = model.fit()
    if use_intercept:
        slope = np.array(results.params)[1]
        slope_interv = slope - np.array(results.conf_int(0.05))[1][0]
        intercept = np.array(results.params)[0]
        intercept_interv = intercept - np.array(results.conf_int(0.05))[0][0]
        slope = round(slope, round_slope)
        slope_interv = round(slope_interv, round_slope)
        intercept = round(intercept, round_intercept)
        intercept_interv = round(intercept_interv, round_intercept)
    else:
        slope = np.array(results.params)[0]
        slope_interv = slope - np.array(results.conf_int(0.05))[0][0]
        intercept = None
        intercept_interv = None
        slope = round(slope, round_slope)
        slope_interv = round(slope_interv, round_slope)

    if use_intercept:
        x = x[:, 1]  # Remove constant to calculate ME and RMSE
    ME = (y - x).mean()
    RMSE = np.sqrt(np.square(y - x).mean())
    return {
        "slope": slope,
        "slope_interv": slope_interv,
        "slope_pretty": f"{slope} ± {slope_interv}",
        "intercept": intercept,
        "intercept_interv": intercept_interv,
        "intercept_pretty": f"{intercept} ± {intercept_interv}",
        "ME": ME,
        # "RMSE": np.sqrt(np.square(y - x * slope).mean()),
        "RMSE": RMSE,
        "R^2": results.rsquared,
    }


F0 = dict((int(float(line.split()[0])), float(line.split()[1])) for line in
          open(pathlib.Path(__file__).parent / "Thuillier2003.txt").read().strip().split("\n"))
