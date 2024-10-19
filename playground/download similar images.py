import datetime

from matplotlib import pyplot as plt

from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo
from light_info.MODIS_database import load_data
from light_info.utils import find_close_timedelta_imgs, intersection_percent
from web.downloader import download_mersi_files, download_modis_files

START = datetime.datetime(2023, 1, 1)
END = datetime.datetime(2024, 10, 1)
# LON = 140
# LAT = 35.5
LON = -43
LAT = 69
MIN_INTERSECTION_PERCENT = 0.3
MAX_TIME_DELTA = datetime.timedelta(minutes=20)

# list_modis = MODISInfo.find_containing_point(START, END, LON, LAT)
list_modis = load_data(
    START, END,
    LON, LAT,
)
list_mersi = MERSIInfo.find_containing_point(START, END, LON, LAT)

pairs = find_close_timedelta_imgs(list_modis, list_mersi, MAX_TIME_DELTA)
print("Timedelta pairs:", len(pairs))

pairs = [pair for pair in pairs if intersection_percent(*pair) > MIN_INTERSECTION_PERCENT]
# [1, 4, 8, 11, 14]
# pairs = [item[1] for item in enumerate(pairs) if item[0] in [1, 4, 8, 11, 14]]
# 8
# pairs = [pairs[8]]
pairs = [pairs[1], pairs[4], pairs[11], pairs[14]]
print("Closely overlapping pairs:", len(pairs))

list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]


for i, info in enumerate(list_mersi):
    preview = info.get_preview()
    plt.imshow(preview)
    plt.title(str(i) + " " + str(info.dt))
    plt.show()

download_mersi_files(
    list_mersi,
    download_l1=True,
    download_l1_geo=True,
    direct_download=False,
)

download_modis_files(
    list_modis,
    download_l1=True,
    download_l1_geo=True,
    download_cloud_mask=True,
)
