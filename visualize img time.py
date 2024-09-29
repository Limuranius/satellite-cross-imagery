import datetime
import matplotlib.pyplot as plt

import get_mersi_list, get_modis_list

start = datetime.date(2024, 8, 31)
end = datetime.date(2024, 9, 27)
lon = 140
lat = 35.5

list_modis = get_modis_list.find_containing_point(start, end, lon, lat)
list_mersi = get_mersi_list.find_containing_point(start, end, lon, lat)

# print(len(list_modis))
# print(len(list_mersi))

modis_dates = [info.dt.timestamp() for info in list_modis]
mersi_dates = [info.dt.timestamp() for info in list_mersi]

plt.plot(modis_dates, [1] * len(modis_dates), "bo")
plt.plot(mersi_dates, [2] * len(mersi_dates), "ro")
plt.show()

# print(*[im.dt for im in list_modis], sep="\n")
# print()
# print(*[im.dt for im in list_mersi], sep="\n")

