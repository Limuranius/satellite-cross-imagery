import datetime
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo
from light_info.Info import Info
from web.downloader import download_mersi_files, download_modis_files


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


start = datetime.date(2024, 9, 1)
end = datetime.date(2024, 9, 27)
lon = 140
lat = 35.5

list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)

pairs = find_close_imgs(list_modis, list_mersi, datetime.timedelta(minutes=30))
list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]
download_mersi_files(list_mersi)
download_modis_files(list_modis)
