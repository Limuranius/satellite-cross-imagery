import datetime

import pandas as pd
import tqdm

import light_info.utils
from light_info.MERSIInfo import MERSIInfo
from processing.MERSIImage import MERSIImage


def get_matched_dts(max_timedelta: datetime.timedelta):
    df = pd.read_csv("../data.csv", sep="\t")
    data = pd.DataFrame({
        "modis_t": pd.to_datetime(df["modis_t"], format="mixed"),
        "aeronet_t": pd.to_datetime(df["aeronet_t"]),
        "aeronet_lat": df["aeronet_lat"],
        "aeronet_lon": df["aeronet_lon"],
    })
    data = data[data["aeronet_t"] >= datetime.datetime(2019, 1, 1)]

    mersi_infos = MERSIInfo.find(
        datetime.datetime(2019, 1, 1),
        datetime.datetime(2021, 10, 1),
    )

    results = []
    for _, row in tqdm.tqdm(data.iterrows()):
        # Находим среднее время между MODIS и AERONET
        # и максимальное отклонение от этого среднего, чтобы расстояние до обоих времён не было больше max_timedelta
        aer_t = row["aeronet_t"]
        modis_t = row["modis_t"]
        mean_dt = aer_t + (modis_t - aer_t) / 2

        diff = abs(aer_t - modis_t)
        if diff > max_timedelta:
            print("Too big timedelta. Skipping...", row["aeronet_t"])
            continue

        info = light_info.utils.find_info_timedelta_containing_point(
            infos=mersi_infos,
            t=mean_dt,
            max_delta=max_timedelta / 2,

            pos=(row["aeronet_lon"], row["aeronet_lat"]),
        )
        if info is not None:
            results.append(info.dt)
    return list(set(results))


downloaded_dts = MERSIImage.all_dts()
matched_dts = get_matched_dts(max_timedelta=datetime.timedelta(hours=3))
print("downloaded_dts", len(downloaded_dts))
print("matched_dts", len(matched_dts))

needs_downloading_dts = sorted(set(matched_dts) - set(downloaded_dts))
print("needs_downloading_dts", len(needs_downloading_dts))


with open("need_download.txt", "w") as file:
    print(*needs_downloading_dts, sep="\n", file=file)