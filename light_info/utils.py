import datetime

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