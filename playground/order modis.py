from light_info.MODIS_database import collect_data, load_data
import datetime as dt

from visuals.map_2d import show_image_boxes

#
# collect_data(
#     dt.date(2023, 1, 1),
#     dt.date(2024, 10, 1)
# )

matches = load_data(
    dt.datetime(2023, 1, 1),
    dt.datetime(2024, 10, 1),
    -43,69,
    # 140, 35
)
print(len(matches))
show_image_boxes(matches)

