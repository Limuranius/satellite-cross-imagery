import datetime
import matplotlib.pyplot as plt

from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo

start = datetime.date(2024, 8, 31)
end = datetime.date(2024, 9, 27)
lon = 140
lat = 35.5

list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)

modis_dates = [info.dt.timestamp() for info in list_modis]
mersi_dates = [info.dt.timestamp() for info in list_mersi]

plt.plot(modis_dates, [1] * len(modis_dates), "bo")
plt.plot(mersi_dates, [2] * len(mersi_dates), "ro")
plt.show()
