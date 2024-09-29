import datetime

import folium

import get_mersi_list, get_modis_list
from utils import random_color, reverse_coords, fix_antimeridian

map_obj = folium.Map()

start = datetime.date(2024, 8, 30)
end = datetime.date(2024, 9, 27)
lon = 140
lat = 35.5

# list_modis = get_modis_list.find_containing_point(start, end, lon, lat)
# img_list = list_modis
list_mersi = get_mersi_list.find_containing_point(start, end, lon, lat)
img_list = list_mersi


folium.Marker([lat, lon]).add_to(map_obj)

for info in img_list:
    folium.Polygon(
        reverse_coords(fix_antimeridian([info.p1, info.p2, info.p3, info.p4])),
        color=random_color(),
    ).add_to(map_obj)

map_obj.show_in_browser()
