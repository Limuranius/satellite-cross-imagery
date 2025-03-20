import datetime

from light_info.MODISInfo import MODISInfo
from web.downloader import download_modis_files

dts = [
    datetime.datetime.fromisoformat('2020-11-22 13:10:00'),
    datetime.datetime.fromisoformat('2020-10-16 12:50:00'),
    datetime.datetime.fromisoformat('2020-10-20 10:50:00'),
    datetime.datetime.fromisoformat('2020-08-04 11:20:00'),
    datetime.datetime.fromisoformat('2020-11-15 04:45:00'),
    datetime.datetime.fromisoformat('2020-08-07 10:10:00'),
    datetime.datetime.fromisoformat('2020-06-14 12:25:00'),
    datetime.datetime.fromisoformat('2020-09-23 11:05:00'),
    datetime.datetime.fromisoformat('2020-11-24 04:40:00'),
    datetime.datetime.fromisoformat('2020-08-07 11:50:00'),
]
list_modis = MODISInfo.from_dts(dts)

download_modis_files(
    list_modis,
    download_l1=True,
    download_l1_geo=True,
    download_cloud_mask=True,
)
