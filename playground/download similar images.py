import datetime

import matplotlib
import pyperclip
from matplotlib import pyplot as plt
from matplotlib.widgets import Button

from light_info.MERSIInfo import MERSIInfo
import visuals.map_2d
from light_info.MODISInfo import MODISInfo
from light_info.MODIS_database import collect_data
from light_info.utils import find_close_timedelta_imgs, intersection_percent, mean_longitude_difference
from web.downloader import download_mersi_files, download_modis_files

START = datetime.datetime(2019, 1, 1)
# END = datetime.datetime(2020, 1, 1)
END = datetime.datetime(2022, 1, 1)
MIN_INTERSECTION_PERCENT = 0.5
MAX_TIME_DELTA = datetime.timedelta(minutes=0)
MIN_LATITUDE = 60

# collect_data(
#     datetime.date(2024, 1, 1),
#     datetime.date(2024, 2, 1),
# )
# exit()

# list_modis = MODISInfo.find(
#     START, END,
#     # (LON, LAT)
# )
list_mersi = MERSIInfo.find(
    START, END,
    # (LON, LAT)
)
exit()

pairs = find_close_timedelta_imgs(list_modis, list_mersi, MAX_TIME_DELTA)
print("Timedelta pairs:", len(pairs))

# pairs = [pair for pair in pairs if intersection_percent(*pair) > MIN_INTERSECTION_PERCENT]
pairs_good = []
for pair in pairs:
    try:
        if intersection_percent(*pair) > MIN_INTERSECTION_PERCENT:
            pairs_good.append(pair)
    except Exception:
        continue
pairs = pairs_good
# pairs.sort(key=lambda pair: intersection_percent(*pair), reverse=True)
pairs.sort(key=lambda pair: mean_longitude_difference(*pair))
print([(intersection_percent(*pair), mean_longitude_difference(*pair)) for pair in pairs])
print([mean_longitude_difference(*pair) for pair in pairs])

pairs = pairs[:3]

# Filtering by latitude
# pairs = [pair for pair in pairs if abs(pair[0].center_coord()[1]) > MIN_LATITUDE]

print("Closely overlapping pairs:", len(pairs))

list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]

# dts = [
#     # datetime.datetime.fromisoformat("2024-01-12 13:50:00"),
#     # datetime.datetime.fromisoformat("2024-01-17 15:40:00"),
#     # datetime.datetime.fromisoformat("2024-01-22 17:30:00"),
#     # datetime.datetime.fromisoformat("2024-01-30 06:35:00"),
#     # datetime.datetime.fromisoformat("2024-02-04 08:20:00"),
#     # datetime.datetime.fromisoformat("2024-02-06 21:15:00"),
#     # datetime.datetime.fromisoformat("2024-02-09 10:10:00"),
#     # datetime.datetime.fromisoformat("2024-02-14 12:00:00"),
#     # datetime.datetime.fromisoformat("2024-02-29 15:45:00"),
#     # datetime.datetime.fromisoformat("2024-04-15 02:00:00"),
#     # datetime.datetime.fromisoformat("2024-04-30 04:15:00"),
#     # datetime.datetime.fromisoformat("2024-05-02 17:00:00"),
#     # datetime.datetime.fromisoformat("2024-05-12 17:15:00"),
#     # datetime.datetime.fromisoformat("2024-05-15 06:10:00"),
#     # datetime.datetime.fromisoformat("2024-06-06 19:35:00"),
#     datetime.datetime.fromisoformat("2024-10-01 20:00:00"),
# ]
# list_modis = MODISInfo.from_dts(dts)
# list_mersi = MERSIInfo.from_dts(dts)

print(len(list_modis))
print(len(list_mersi))

print(*[item.dt for item in list_mersi], sep="\n")


visuals.map_2d.show_image_boxes(list_modis + list_mersi)


def show_mersi_previews():
    matplotlib.rcParams['figure.figsize'] = (30, 15)
    for i, info in enumerate(list_mersi):
        preview = info.get_preview()
        pyperclip.copy(str(info.dt))
        plt.imshow(preview)
        plt.title(str(i) + " " + str(info.dt))
        plt.show()
# show_mersi_previews()

# download_mersi_files(
#     list_mersi,
#     download_l1=True,
#     download_l1_geo=True,
#     direct_download=False,
# )

# download_modis_files(
#     list_modis,
#     download_l1=True,
#     download_l1_geo=True,
#     download_cloud_mask=True,
# )
