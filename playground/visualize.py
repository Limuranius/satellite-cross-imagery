import datetime


from light_info.MERSIInfo import MERSIInfo
import folium
from light_info.MODISInfo import MODISInfo
from utils import random_color, reverse_coords, fix_antimeridian

map_obj = folium.Map()

start = datetime.date(2024, 1, 1)
end = datetime.date(2024, 4, 1)
lon = -43
lat = 69

# list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
# img_list = list_modis

list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)
img_list = list_mersi


folium.Marker([lat, lon]).add_to(map_obj)

for info in img_list:
    folium.Polygon(
        reverse_coords(fix_antimeridian([info.p1, info.p2, info.p3, info.p4])),
        color=random_color(),
    ).add_to(map_obj)

map_obj.show_in_browser()
