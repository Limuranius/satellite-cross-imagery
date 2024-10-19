import folium

from light_info.Info import Info
from utils import reverse_coords, fix_antimeridian, random_color


def show_image_boxes(
        infos: list[Info],
        map_obj: folium.Map = None,
) -> folium.Map:
    if map_obj is None:
        map_obj = folium.Map()
    for info in infos:
        folium.Polygon(
            reverse_coords(fix_antimeridian([info.p1, info.p2, info.p3, info.p4])),
            color=random_color(),
        ).add_to(map_obj)

    map_obj.show_in_browser()
    return map_obj
