import folium

from custom_types import LonLat
from light_info.Info import Info
from processing.SatelliteImage import SatelliteImage
import utils
import plotly.graph_objects as go


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
            utils.reverse_coords(utils.fix_antimeridian(corners)),
            color=utils.random_color(),
            popup=f"{obj.dt}"
        ).add_to(map_obj)

    # map_obj.show_in_browser()
    return map_obj


def plotly_show(
        objects: list[Info | SatelliteImage],
        points: list[LonLat] = None,
        point_names: list[str] = None,
):
    if points is None:
        points = []
    if point_names is None:
        point_names = [""] * len(points)
    boxes: list[list[LonLat]] = []
    for obj in objects:
        if isinstance(obj, Info):
            corners = [obj.p1, obj.p2, obj.p3, obj.p4]
        elif isinstance(obj, SatelliteImage):
            corners = obj.get_corners_coords()
        else:
            raise Exception()
        boxes.append(utils.fix_antimeridian(corners))

    fig = go.Figure()

    # Add boxes on the map
    for box in boxes:
        polygon_lons = [p[0] for p in box]
        polygon_lats = [p[1] for p in box]
        polygon_lons.append(polygon_lons[0])
        polygon_lats.append(polygon_lats[0])
        fig.add_trace(go.Scattermap(
            name="Polygon",
            mode="lines",
            lon=polygon_lons,
            lat=polygon_lats,
            marker={'size': 10, 'color': 'red'},
            line=dict(width=3, color='blue'),
            fill='toself',
            fillcolor='rgba(0, 100, 255, 0.3)',
            opacity=0.8
        ))

    # Add separate point
    for point, point_name in zip(points, point_names):
        fig.add_trace(go.Scattermap(
            name="Separate Point",
            mode="markers",
            lon=[point[0]],
            lat=[point[1]],
            marker={'size': 15, 'color': 'green', 'symbol': 'star'},
            text=[point_name],
            hoverinfo='text'
        ))

    fig.update_layout(
        mapbox_style="open-street-map",
        # mapbox=dict(
        #     center=dict(lon=sum(all_lons) / len(all_lons),
        #                 lat=sum(all_lats) / len(all_lats)),
        #     zoom=3
        # ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=True
    )
    return fig
