import datetime


from light_info.utils import find_similar_images
import folium
from utils import random_color, reverse_coords, fix_antimeridian

lon, lat = -43, 65
pairs = find_similar_images(
    start=datetime.date(2023, 10, 1),
    end=datetime.date(2024, 4, 1),
    lon=lon,
    lat=lat,
    min_intersection_percent=0.3,
    max_time_delta=datetime.timedelta(minutes=10),
)
pairs = pairs[:1]

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
