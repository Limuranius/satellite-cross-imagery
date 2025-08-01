import pandas as pd

import processing.algorithms
from utils import F0

import paths

df = pd.read_csv(paths.DATA_DIR / "data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])


lwnfq_cols = [col for col in df.columns if "Lwn_f/Q" in col]

for col in lwnfq_cols:
    wv = int(col.split("[")[1][:-3])
    rrs = df[col] * 10 / F0[wv]
    df[f"aeronet_Rrs[{wv}nm]"] = rrs


# Объединяем зелёные Rrs для AERONET с пропусками в один столбец
df["aeronet_green_Rrs"] = df['aeronet_Rrs[551nm]'].fillna(df['aeronet_Rrs[555nm]']).fillna(df['aeronet_Rrs[560nm]'])

# Добавляем хлорофилл из Rrs
df["aeronet_chlor_a_from_rrs"] = processing.algorithms.chl_oc3([
    df["aeronet_Rrs[443nm]"],
    df["aeronet_Rrs[490nm]"],
    df["aeronet_green_Rrs"],
])

df.to_csv(paths.DATA_DIR / "data.csv", sep="\t", index=False)