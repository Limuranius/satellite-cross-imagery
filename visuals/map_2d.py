import folium

from light_info.Info import Info
from processing.SatelliteImage import SatelliteImage
from utils import reverse_coords, fix_antimeridian, random_color


def show_image_boxes(
        objects: list[Info | SatelliteImage],
        map_obj: folium.Map = None,
) -> folium.Map:
    if map_obj is None:
        map_obj = folium.Map()
    for obj in objects:
        if isinstance(obj, Info):
            corners = [obj.p1, obj.p2, obj.p3, obj.p4]
        elif isinstance(obj, SatelliteImage):
            corners = obj.get_corners_coords()
        else:
            raise Exception()
        # folium.Marker(corners[0][::-1], "p1").add_to(map_obj)
        # folium.Marker(corners[1][::-1], "p2").add_to(map_obj)
        # folium.Marker(corners[2][::-1], "p3").add_to(map_obj)
        # folium.Marker(corners[3][::-1], "p4").add_to(map_obj)
        folium.Polygon(
            reverse_coords(fix_antimeridian(corners)),
            color=random_color(),
            popup=f"{obj.dt}"
        ).add_to(map_obj)

    # map_obj.show_in_browser()
    return map_obj

