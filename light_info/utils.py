import bisect
import datetime

import folium

import visuals.map_2d
from custom_types import LonLat
from light_info.Info import Info
import utils
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo


def find_close_timedelta_imgs(
        l1: list[Info],
        l2: list[Info],
        max_diff: datetime.timedelta
) -> list[tuple[Info, Info]]:
    l1 = sorted(l1, key=lambda info: info.dt)
    l2 = sorted(l2, key=lambda info: info.dt)
    result = []
    while l1 and l2:
        t1 = l1[0].dt
        t2 = l2[0].dt
        if abs(t1 - t2) <= max_diff:
            result.append((l1.pop(0), l2.pop(0)))
        else:
            if t1 < t2:
                l1.pop(0)
            else:
                l2.pop(0)
    return result


def intersection_percent(info1: Info, info2: Info) -> float:
    return utils.intersection_percent(
        [info1.p1, info1.p2, info1.p3, info1.p4],
        [info2.p1, info2.p2, info2.p3, info2.p4]
    )


def mean_longitude_difference(info1: Info, info2: Info) -> float:
    lon1_upper = (info1.p1[0] + info1.p2[0]) / 2
    lon1_lower = (info1.p3[0] + info1.p4[0]) / 2
    lon2_upper = (info2.p1[0] + info2.p2[0]) / 2
    lon2_lower = (info2.p3[0] + info2.p4[0]) / 2

    return (lon1_upper - lon2_upper) ** 2 + (lon1_lower - lon2_lower) ** 2

    # lon1 = (info1.p1[0] + info1.p2[0] + info1.p3[0] + info1.p4[0]) / 4
    # lon2 = (info2.p1[0] + info2.p2[0] + info2.p3[0] + info2.p4[0]) / 4
    # return abs(lon1 - lon2)


def find_similar_images(
        start: datetime.date,
        end: datetime.date,
        lon: float,
        lat: float,
        min_intersection_percent: float,
        max_time_delta: datetime.timedelta,
) -> list[tuple[MERSIInfo, MODISInfo]]:
    list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
    list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)

    # Filtering by time difference
    pairs = find_close_timedelta_imgs(list_modis, list_mersi, max_time_delta)
    print("Timedelta pairs:", len(pairs))

    # Filtering by overlapping amount
    pairs = [pair for pair in pairs if intersection_percent(*pair) > min_intersection_percent]
    print("Closely overlapping pairs:", len(pairs))

    return pairs


def find_info_timedelta(
        infos: list[Info],
        t: datetime.datetime,
        max_delta: datetime.timedelta,
) -> list[Info]:
    """Находит все info, которые по времени различаются с t максимум на max_delta"""
    infos = sorted(infos, key=lambda info: info.dt)
    i = bisect.bisect_left(infos, t, key=lambda info: info.dt)
    res = []
    left_i = i
    while 0 <= left_i < len(infos) and abs(infos[left_i].dt - t) <= max_delta:
        res.append(infos[left_i])
        left_i -= 1
    right_i = i + 1
    while 0 <= right_i < len(infos) and abs(infos[right_i].dt - t) <= max_delta:
        res.append(infos[right_i])
        right_i += 1
    return res


def find_info_timedelta_containing_point(
        infos: list[Info],
        t: datetime.datetime,
        max_delta: datetime.timedelta,
        pos: LonLat
) -> Info | None:
    infos = find_info_timedelta(infos, t, max_delta)
    for info in infos:
        if info.contains_pos(*pos):
            return info
    return None



