import bisect

import pandas as pd
from pyorbital.orbital import Orbital
from matplotlib import pyplot as plt

df = pd.read_csv("data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])

tles = open("aqua_tles_2019-2020.txt").readlines()
tles = [(tles[i + 1].strip(), tles[i + 2].strip()) for i in range(0, len(tles), 3)]
orbs = [Orbital("AQUA", line1=tle[0], line2=tle[1]) for tle in tles]


for i, row in df.iterrows():
    orb = orbs[
        min(bisect.bisect_left(
            orbs,
            row["modis_t"],
            key=lambda orb: orb.tle.epoch
        ), len(orbs) - 1)
    ]
    diff = abs(orb.tle.epoch - row["modis_t"]).days
    if diff > 1:
        print(row["modis_t"])
        continue

    az, elev = orb.get_observer_look(
        utc_time=row["modis_t"],
        lon=row["aeronet_lon"],
        lat=row["aeronet_lat"],
        alt=0
    )
    zen = 90 - elev

    df.loc[i, "modis_zenith"] = zen
    df.loc[i, "modis_azimuth"] = az


df.to_csv("data.csv", sep="\t", index=False)