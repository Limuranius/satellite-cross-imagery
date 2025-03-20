from datetime import datetime

import pandas as pd
import pyorbital.orbital
from matplotlib import pyplot as plt

df = pd.read_csv("data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])

for i, row in df.iterrows():
    az, zen = pyorbital.orbital.get_observer_look(
        sat_lon=row["modis_lon"],
        sat_lat=row["modis_lat"],
        sat_alt=750,
        utc_time=row["modis_t"],
        lon=row["aeronet_lon"],
        lat=row["aeronet_lat"],
        alt=0
    )

    df.loc[i, "modis_zenith"] = zen
    df.loc[i, "modis_azimuth"] = az


df.to_csv("data.csv", sep="\t")