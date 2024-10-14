import datetime


from aeronet import stations_positions
from light_info.MERSIInfo import MERSIInfo
import folium
from light_info.MODISInfo import MODISInfo
from light_info.utils import find_close_imgs, intersection_percent
from utils import random_color, reverse_coords, fix_antimeridian

START = datetime.date(2019, 9, 1)
END = datetime.date(2019, 10, 1)
LON, LAT, _ = stations_positions.positions["Ieodo_Station"]
MIN_INTERSECTION_PERCENT = 0.3
MAX_TIME_DELTA = datetime.timedelta(minutes=10)

list_modis = MODISInfo.find_containing_point(START, END, LON, LAT)
list_mersi = MERSIInfo.find_containing_point(START, END, LON, LAT)

pairs = find_close_imgs(list_modis, list_mersi, MAX_TIME_DELTA)
pairs = [pair for pair in pairs if intersection_percent(*pair) > MIN_INTERSECTION_PERCENT]
pairs = pairs[:1]

list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]

map_obj = folium.Map()
folium.Marker([LAT, LON]).add_to(map_obj)

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
