import datetime
import matplotlib.pyplot as plt

from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo

start = datetime.date(2023, 10, 1)
end = datetime.date(2024, 4, 1)
lon = -43
lat = 67

list_modis = MODISInfo.find_containing_point(start, end, lon, lat)
list_mersi = MERSIInfo.find_containing_point(start, end, lon, lat)

modis_dates = [info.dt.timestamp() for info in list_modis]
mersi_dates = [info.dt.timestamp() for info in list_mersi]

plt.plot(modis_dates, [1] * len(modis_dates), "bo")
plt.plot(mersi_dates, [2] * len(mersi_dates), "ro")
plt.show()
