import datetime

import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt

from processing.MERSIImage import MERSIImage
from processing.preprocessing import get_mersi_dates
import seaborn as sns


def outliers_mask(data):
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    threshold = 1.5 * iqr
    return (data < q1 - threshold) | (data > q3 + threshold)


def outliers_2d_mask(data_2d: np.ndarray):
    data = data_2d.flatten()
    mask_1d = outliers_mask(data)
    return mask_1d.reshape(data_2d.shape)


def process_image(
        image: MERSIImage,
):
    for i, row in iterate_rows_timedelta_within_image(image):
        site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])

        # Вырезаем окно вокруг станции
        radius = 2
        area_idx = [
            slice(max(0, site_i - radius), site_i + radius + 1),
            slice(max(0, site_j - radius), site_j + radius + 1),
        ]
        big_area_idx = [
            slice(max(0, site_i - 20), site_i + 20 + 1),
            slice(max(0, site_j - 20), site_j + 20 + 1),
        ]

        band13 = image.get_band("13")
        color = image.colored_image()
        color_small = np.array(color[*area_idx])
        color_big = color[*big_area_idx]
        color_big[20, 20] = (255, 0, 0)

        reflectance13 = band13.reflectance[*area_idx]
        mask = reflectance13 < 0.03
        if mask.sum() == 0:  # Есть случаи, когда альбедо >3%, но вода всё равно однородная
            mask = ~outliers_2d_mask(reflectance13)
        else:
            mask = ~outliers_2d_mask(reflectance13) & mask
        pixels = reflectance13[mask]
        if pixels.std() > 0.002:  # Не удалось убрать выбросы, всё убираем
            mask = np.zeros_like(mask)
        mask = mask & (reflectance13 < 0.1)  # Не брать однородные облака
        pixels = reflectance13[mask]


        _, ax = plt.subplots(ncols=3, nrows=2, figsize=(20, 8))
        sns.heatmap(reflectance13, center=0, annot=True, ax=ax[0, 0], fmt=".3f")
        ax[0, 1].imshow(color_small)
        ax[0, 2].imshow(color_big)
        ax[1, 0].imshow(mask)
        ax[1, 1].boxplot(pixels)
        ax[1, 2].text(0.1, 0.1, f"n={len(pixels)}\nstd={pixels.std():.6f}\nmean={pixels.mean():.3f}\nmedian={np.median(pixels):.3f}\ndt={image.dt}")
        plt.tight_layout()
        # plt.show()
        plt.savefig(f"cloud_masks/{i}.jpg", dpi=200)
        plt.close()

def homogeneous_pixels_mask(image: MERSIImage, area_idx):
    band13 = image.get_band("13")
    reflectance13 = band13.reflectance[*area_idx]
    mask = reflectance13 < 0.03
    if mask.sum() == 0:  # Есть случаи, когда альбедо >3%, но вода всё равно однородная
        mask = ~outliers_2d_mask(reflectance13)
    else:
        mask = ~outliers_2d_mask(reflectance13) & mask
    pixels = reflectance13[mask]
    if pixels.std() > 0.002:
        return None  # Слишком зашумлено, невозможно убрать выбросы, потому что не понятно, что является выбросом
    mask = mask & (reflectance13 < 0.1)  # Не брать однородные облака
    return mask


def iterate_rows_timedelta_within_image(image: MERSIImage):
    timedelta = (df["aeronet_t"] - image.dt).abs()
    good_timedelta = df[timedelta <= datetime.timedelta(hours=1)]
    for i, row in good_timedelta.iterrows():
        if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
            yield i, row


BANDS = ["8"]
df = pd.read_csv("data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
df = df[df["modis_zenith"].notna()]
if __name__ == '__main__':
    mersi_dts = get_mersi_dates()
    for mersi_dt in tqdm.tqdm(mersi_dts):
        for band in BANDS:
            image = MERSIImage.from_dt(mersi_dt, band)
            process_image(image)

    df = df[df["mersi_t"] == df["mersi_t"]]
    df.to_csv("data_with_mersi.csv", sep="\t", index=False)
