import pickle

import pandas as pd
import tqdm

import paths
import processing.MERSIImage

with open("atmosphere.pkl", "rb") as file:
    results = pickle.load(file)


INPUT_PATH = paths.DATA_DIR / "data_with_mersi_2.csv"
OUTPUT_PATH = paths.DATA_DIR / "data_with_mersi_2.csv"


df = pd.read_csv(INPUT_PATH, sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
df = df[df["modis_zenith"].notna()]


for band in tqdm.tqdm(results):
    wl = processing.MERSIImage.MERSI_BANDS_WAVELEN[band]
    for r in results[band]:
        mersi_t = r["mersi_t"]
        aeronet_t = r["aeronet_t"]
        out_6s = r["6S_output"]
        mask = df["aeronet_t"] == aeronet_t

        apparent_radiance = out_6s["values"]["apparent_radiance"]
        apparent_reflectance = out_6s["values"]["apparent_reflectance"]
        atm_radiance = out_6s["values"]["atmospheric_intrinsic_radiance"]

        df.loc[mask, f"mersi_6S_radiance[{wl}nm]"] = apparent_radiance
        df.loc[mask, f"mersi_6S_reflectance[{wl}nm]"] = apparent_reflectance
        df.loc[mask, f"mersi_6S_atm_rad[{wl}nm]"] = atm_radiance

df = df[df["mersi_t"] == df["mersi_t"]]
df.to_csv(OUTPUT_PATH, sep="\t", index=False)