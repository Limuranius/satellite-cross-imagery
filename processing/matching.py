import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from global_land_mask import globe

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
) -> list[tuple[int, int], tuple[int, int]]:
    coords = np.array([image_mersi.longitude, image_mersi.latitude])
    coords = coords.transpose((1, 2, 0))
    coords = coords.reshape((-1, 2))  # flatten
    fast_match = image_modis.geo_kdtree.query(coords)
    distance, indices = fast_match

    max_distance = 0.03

    result = []
    for i in range(len(indices)):
        if distance[i] > max_distance:
            continue
        mersi_i, mersi_j = np.unravel_index(i, image_mersi.latitude.shape)
        modis_i, modis_j = np.unravel_index(indices[i], image_modis.latitude.shape)
        result.append(((mersi_i, mersi_j), (modis_i, modis_j)))
    return result


def filter_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
        max_zenith_diff: int,
        max_zenith: int,
) -> list[tuple[int, int], tuple[int, int]]:
    result = []

    for mersi_coord, modis_coord in tqdm.tqdm(pixels, desc="Filtering matching pixels"):
        lon = image_mersi.longitude[*mersi_coord]
        lat = image_mersi.latitude[*mersi_coord]

        # Check cloud mask
        if image_modis.cloud_mask[*modis_coord] != 3:
            continue

        # Check zenith difference
        zenith_mersi = image_mersi.sensor_zenith[*mersi_coord]
        zenith_modis = image_modis.sensor_zenith[*modis_coord]
        if abs(zenith_modis - zenith_mersi) > max_zenith_diff or zenith_mersi > max_zenith:
            continue

        # Skip pixels that don't contain water
        if globe.is_land(lat, lon):
            continue

        result.append((mersi_coord, modis_coord))

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


def matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]]
) -> pd.DataFrame:
    df = pd.DataFrame(
        index=range(len(pixels)),
        columns=["mersi_rad", "modis_rad", "rad_diff", "mersi_senz", "modis_senz"]
    )
    for i, (mersi_coord, modis_coord) in tqdm.tqdm(list(enumerate(pixels)), desc="Creating statistics"):
        df.loc[i] = {
            "mersi_rad": image_mersi.radiance[*mersi_coord],
            "modis_rad": image_modis.radiance[*modis_coord],
            "rad_diff": image_mersi.radiance[*mersi_coord] - image_modis.radiance[*modis_coord],
            "mersi_senz": image_mersi.sensor_zenith[*mersi_coord],
            "modis_senz": image_modis.sensor_zenith[*modis_coord],
        }
    return df
