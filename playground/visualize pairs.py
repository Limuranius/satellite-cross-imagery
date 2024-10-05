import datetime

import folium

from aeronet import stations_positions
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo
from light_info.Info import Info
from utils import random_color, reverse_coords, fix_antimeridian


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


start = datetime.date(2024, 9, 11)
end = datetime.date(2024, 9, 13)
lon, lat, _ = stations_positions.positions["Ieodo_Station"]

list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)

pairs = find_close_imgs(list_modis, list_mersi, datetime.timedelta(minutes=10))
list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]

map_obj = folium.Map()
folium.Marker([lat, lon]).add_to(map_obj)

for mersi, modis in zip(list_mersi, list_modis):
    color = random_color()
    folium.Polygon(
        reverse_coords(fix_antimeridian([mersi.p1, mersi.p2, mersi.p3, mersi.p4])),
        color=color,
        popup="MERSI",
    ).add_to(map_obj)
    folium.Polygon(
        reverse_coords(fix_antimeridian([modis.p1, modis.p2, modis.p3, modis.p4])),
        color=color,
        popup="MODIS",
    ).add_to(map_obj)

map_obj.show_in_browser()