from datetime import datetime

import matplotlib.pyplot as plt

from processing import MODISImage
from processing import MERSIImage
from processing.load_imagery import iterate_close_images


def see_modis():
    fig, ax = plt.subplots(nrows=4, ncols=4)

    for k, band in enumerate(MODISImage.BANDS):
        i = k // 4
        j = k % 4

        img_modis = MODISImage.MODISImage(
            "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B/MYD021KM.A2024248.1425.061.2024249173029.hdf",
            "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B GEO/MYD03.A2024248.1425.061.2024249171339.hdf",
            band,
        )

        ax[i][j].imshow(img_modis.radiance)
        ax[i][j].set_title(band)

    plt.show()


def see_mersi():
    fig, ax = plt.subplots(nrows=4, ncols=4)

    for k, band in enumerate(MERSIImage.BANDS):
        i = k // 4
        j = k % 4

        img_mersi = MERSIImage.MERSIImage(
            "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1/FY3D_MERSI_GBAL_L1_20240904_1420_1000M_MS.HDF",
            "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1 GEO/FY3D_MERSI_GBAL_L1_20240904_1420_GEO1K_MS.HDF",
            band,
        )

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
# see_modis()
see_water_mask()