import folium
import matplotlib.pyplot as plt
import tqdm
import visuals.map_2d
import light_info.utils
import pandas as pd
from datetime import datetime, date, timedelta

from light_info.MERSIInfo import MERSIInfo

df = pd.read_csv("data.csv", sep="\t")
data = pd.DataFrame({
    "modis_t": pd.to_datetime(df["modis_t"], format="mixed"),
    "aeronet_t": pd.to_datetime(df["aeronet_t"]),
    "aeronet_lat": df["aeronet_lat"],
    "aeronet_lon": df["aeronet_lon"],
})
data = data[data["aeronet_t"] > datetime(2019, 1, 1)]
# data = data.head(200)

mersi_infos = MERSIInfo.find(
    datetime(2019, 1, 1),
    datetime(2022, 1, 1),
)

map_obj = folium.Map()
results = []
for _, row in tqdm.tqdm(data.iterrows()):
    info = light_info.utils.find_info_timedelta_containing_point(
        mersi_infos,
        row["aeronet_t"],
        timedelta(hours=1),
        (row["aeronet_lon"], row["aeronet_lat"])
    )

    # Рисуем график
    if info is None:
        # print(_)
        # results.append(None)
        pass
    else:
        visuals.map_2d.show_image_boxes([info], map_obj=map_obj)
        folium.Marker((row["aeronet_lat"], row["aeronet_lon"])).add_to(map_obj)
        results.append(info.dt)

map_obj.show_in_browser()
# print("Not None count:", sum([i is not None for i in results]))
# fig, ax = plt.subplots(ncols=2)
# ax[0].plot(results)
# ax[1].hist([i for i in results if i is not None])
# plt.show()

#
# with open("need_download.txt", "w") as file:
#     print(*sorted(list(set(results))), sep="\n", file=file)
