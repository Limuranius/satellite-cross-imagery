import datetime

from matplotlib import pyplot as plt

from light_info.MERSIInfo import MERSIInfo
import visuals.map_2d
from light_info.MODISInfo import MODISInfo
from light_info.MODIS_database import collect_data
from light_info.utils import find_close_timedelta_imgs, intersection_percent
from web.downloader import download_mersi_files, download_modis_files

START = datetime.datetime(2019, 1, 4, 22)
END = datetime.datetime(2019, 1, 5)
# LON = 140
# LAT = 35.5
LON = -43
LAT = 69
MIN_INTERSECTION_PERCENT = 0.4
MAX_TIME_DELTA = datetime.timedelta(minutes=0)

# collect_data(
#     datetime.date(2019, 1, 1),
#     datetime.date(2019, 6, 1),
# )
list_modis = MODISInfo.find(
    START, END,
    # (LON, LAT)
)
list_mersi = MERSIInfo.find(
    START, END,
    # (LON, LAT)
)

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
# pairs = pairs[:-3]
print("Closely overlapping pairs:", len(pairs))

list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]


visuals.map_2d.show_image_boxes(list_modis + list_mersi)


# for i, info in enumerate(list_mersi):
#     preview = info.get_preview()
#     plt.imshow(preview)
#     plt.title(str(i) + " " + str(info.dt))
#     plt.show()

# download_mersi_files(
#     list_mersi,
#     download_l1=True,
#     download_l1_geo=True,
#     direct_download=False,
# )
#
# download_modis_files(
#     list_modis,
#     download_l1=True,
#     download_l1_geo=True,
#     download_cloud_mask=True,
# )
