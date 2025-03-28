import pandas as pd

from utils import F0

df = pd.read_csv("data_with_mersi.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])


lwnfq_cols = [col for col in df.columns if "Lwn_f/Q" in col]

for col in lwnfq_cols:
    wv = int(col.split("[")[1][:-3])
    rrs = df[col] / F0[wv] * 100
    df[f"aeronet_Rrs[{wv}nm]"] = rrs

df.to_csv("data_with_mersi.csv", sep="\t", index=False)