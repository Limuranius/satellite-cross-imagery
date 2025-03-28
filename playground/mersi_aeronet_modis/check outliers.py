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

        good_pixels_mask = homogeneous_pixels_mask(image, area_idx)
        if good_pixels_mask is None:
            continue

        # # Посмотреть маску хороших пикселей
        # _, ax = plt.subplots(ncols=2, figsize=(10, 20))
        # # ax[0].imshow(image.counts[*area_idx])
        # sns.heatmap(image.counts[*area_idx], center=0, annot=True, ax=ax[0])
        # ax[1].imshow(good_pixels_mask.reshape((5, 5)))
        # plt.show()


def homogeneous_pixels_mask(image: MERSIImage, area_idx):
    band13 = image.get_band("13")
    area = band13.counts[*area_idx]
    pixels = area.flatten()
    good_pixels_mask = pixels <= 4096  # Убираем битые пиксели
    # if pixels[good_pixels_mask].std() < 100:  # Изображение изначально было однородным
    #     return good_pixels_mask
    good_pixels_mask &= ~outliers_mask(pixels)  # Убираем выбросы

    # Посмотреть маску хороших пикселей
    _, ax = plt.subplots(ncols=3, figsize=(20, 10))
    sns.heatmap(area, center=0, annot=True, ax=ax[0], fmt=".0f")
    sns.heatmap(image.counts[*area_idx], center=0, annot=True, ax=ax[2], fmt=".0f")
    ax[1].imshow(good_pixels_mask.reshape((5, 5)))
    plt.show()

    if pixels[good_pixels_mask].std() < 100:
        return good_pixels_mask
    return None  # Слишком зашумлено, невозможно убрать выбросы, потому что не понятно, что является выбросом


def iterate_rows_timedelta_within_image(image: MERSIImage):
    timedelta = (df["aeronet_t"] - image.dt).abs()
    good_timedelta = df[timedelta <= datetime.timedelta(hours=1)]
    for i, row in good_timedelta.iterrows():
        if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
            yield i, row


# BANDS = [
#     "8", "9", "10", "11",
#     "12", "13", "14", "15"
# ]
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
