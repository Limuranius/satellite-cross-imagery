import pickle
import matplotlib.pyplot as plt
import numpy as np
from zarr import zeros

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from global_land_mask import globe
import tqdm


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        max_zenith_diff: int
) -> list[tuple[int, int], tuple[int, int]]:
    result = []
    with tqdm.tqdm(total=2000 * 2048, desc="Searching for matching pixels") as pbar:
        for i in range(2000):  # MERSI height
            for j in range(2048):  # MERSI width
                pbar.update(1)

                lon = image_mersi.longitude[i, j]
                lat = image_mersi.latitude[i, j]

                # Skip pixels that don't contain water
                if globe.is_land(lat, lon):
                    continue

                # Find matching pixel in other image
                if not image_modis.contains_pos(lon, lat):
                    continue
                modis_i, modis_j = image_modis.get_closest_pixel(lon, lat)

                # Check zenith difference
                zenith_mersi = image_mersi.sensor_zenith[i, j]
                zenith_modis = image_modis.sensor_zenith[modis_i, modis_j]
                if abs(zenith_modis - zenith_mersi) > max_zenith_diff:
                    continue

                result.append(((i, j), (modis_i, modis_j)))
    return result


def visualize_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]]
):
    mask_mersi = np.zeros_like(image_mersi.radiance, dtype=bool)
    mask_modis = np.zeros_like(image_modis.radiance, dtype=bool)
    for (mersi_i, mersi_j), (modis_i, modis_j) in pixels:
        mask_mersi[mersi_i, mersi_j] = True
        mask_modis[modis_i, modis_j] = True

    im1 = image_mersi.radiance.copy()
    im2 = image_mersi.radiance.copy()
    im2[~mask_mersi] = 0
    im3 = image_modis.radiance.copy()
    im4 = image_modis.radiance.copy()
    im4[~mask_modis] = 0

    fig, ax = plt.subplots(ncols=4)
    ax[0].imshow(im1)
    ax[1].imshow(im2)
    ax[2].imshow(im3)
    ax[3].imshow(im4)
    plt.show()



img_mersi = MERSIImage(
    "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1/FY3D_MERSI_GBAL_L1_20240912_0350_1000M_MS.HDF",
    "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1 GEO/FY3D_MERSI_GBAL_L1_20240912_0350_GEO1K_MS.HDF",
    "8",
)

img_modis = MODISImage(
    "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B/MYD021KM.A2024256.0345.061.2024256152131.hdf",
    "8"
)

with open("pixels.pkl", "rb") as file:
    pixels = pickle.load(file)

visualize_matching_pixels(
    img_mersi,
    img_modis,
    pixels
)

# pixels = get_matching_pixels(img_mersi, img_modis, 100)
# print(len(pixels))
# with open("pixels.pkl", "wb") as file:
#     pickle.dump(pixels, file)
