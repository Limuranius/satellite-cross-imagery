import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import load_srf

def visualize_mersi():
    mersi_df = []
    mersi_bands = [
        *range(8, 15)
    ]
    for band in mersi_bands:
        df = load_srf.load_mersi(band)
        df["band"] = band
        mersi_df.append(df)
    mersi_df = pd.concat(mersi_df)


    sns.relplot(mersi_df, x="wavelength", y="srf", hue="band", kind="line", palette="tab10")
    plt.show()


def visualize_bands_difference():
    band_pairs = [
        (8, 8),
        (9, 9),
        (10, 10),
        # (11, 12),
        # (12, 13),
        # (12, 14),
    ]
    total_df = []
    for mersi_band, modis_band in band_pairs:
        df_mersi = load_srf.load_mersi(mersi_band)
        df_mersi["band_pair"] = f"{mersi_band} {modis_band}"
        df_mersi["sensor"] = "MERSI-2"

        df_modis = load_srf.load_modis(modis_band)
        df_modis["band_pair"] = f"{mersi_band} {modis_band}"
        df_modis["sensor"] = "MODIS AQUA"

        total_df.append(df_mersi)
        total_df.append(df_modis)

        mersi_area = np.trapz(y=df_mersi["srf"], x=df_mersi["wavelength"])
        modis_area = np.trapz(y=df_modis["srf"], x=df_modis["wavelength"])
        print(mersi_area / modis_area)
    total_df = pd.concat(total_df)
    sns.relplot(
        total_df,
        x="wavelength",
        y="srf",
        hue="sensor",
        col="band_pair",
        kind="line",
        facet_kws={'sharey': True, 'sharex': False}
    )
    plt.show()


visualize_bands_difference()