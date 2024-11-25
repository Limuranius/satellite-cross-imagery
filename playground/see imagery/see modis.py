from datetime import datetime

import matplotlib.pyplot as plt

from processing import MODISImage
from processing import MERSIImage
from processing.load_imagery import iterate_close_images


def see_modis():
    fig, ax = plt.subplots(nrows=4, ncols=4)

    for k, band in enumerate(MODISImage.MODIS_BANDS):
        i = k // 4
        j = k % 4

        img_modis = MODISImage.MODISImage.from_dt(datetime.fromisoformat("2024-01-07 12:00:00"), band)

        ax[i][j].imshow(img_modis.radiance)
        ax[i][j].set_title(band)

    plt.show()


def see_mersi():
    fig, ax = plt.subplots(nrows=4, ncols=4)

    for k, band in enumerate(MERSIImage.MERSI_2_BANDS):
        i = k // 4
        j = k % 4

        img_mersi = MERSIImage.MERSIImage.from_dt(datetime(2024, 2, 11, 23), band,)

        ax[i][j].imshow(img_mersi.radiance)
        ax[i][j].set_title(band)

    plt.show()


def see_water_mask():
    for _, img_modis in iterate_close_images(
        "8", "17",
        interval=(datetime(2024, 9, 4), datetime(2024, 9, 5)),
    ):
        _, ax = plt.subplots(ncols=2)
        ax[0].imshow(img_modis.reflectance)
        ax[1].imshow(img_modis.water_mask)
        plt.show()


# see_mersi()
see_modis()
# see_water_mask()