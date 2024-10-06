import datetime

from light_info.Info import Info
import utils


def find_close_imgs(
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
        if abs(t1 - t2) < max_diff:
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
