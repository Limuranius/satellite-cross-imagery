import datetime
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo
from light_info.utils import find_close_imgs, intersection_percent
from web.downloader import download_mersi_files, download_modis_files

START = datetime.date(2024, 9, 11)
END = datetime.date(2024, 9, 13)
LON = 140
LAT = 35.5
MIN_INTERSECTION_PERCENT = 0.3
MAX_TIME_DELTA = datetime.timedelta(minutes=30)

list_modis = MODISInfo.find_containing_point(START, END, LON, LAT)
list_mersi = MERSIInfo.find_containing_point(START, END, LON, LAT)

pairs = find_close_imgs(list_modis, list_mersi, MAX_TIME_DELTA)
pairs = [pair for pair in pairs if intersection_percent(*pair) > MIN_INTERSECTION_PERCENT]

list_modis = [pair[0] for pair in pairs]
list_mersi = [pair[1] for pair in pairs]

# download_mersi_files(list_mersi, download_l1_geo=True)
download_modis_files(
    list_modis,
    download_l1=False,
    download_l1_geo=False,
    download_cloud_mask=True
)
