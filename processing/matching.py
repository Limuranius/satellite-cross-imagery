import os.path
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from global_land_mask import globe

import paths
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
) -> list[tuple[int, int], tuple[int, int]]:
    coords = np.array([image_mersi.longitude, image_mersi.latitude])
    coords = coords.transpose((1, 2, 0))
    coords = coords.reshape((-1, 2))  # flatten
    print("Matching pixels...")
    fast_match = image_modis.geo_kdtree.query(coords)
    print("Done...")
    distance, indices = fast_match

    max_distance = 0.03

    mersi_i, mersi_j = np.unravel_index(list(range(len(indices))), image_mersi.latitude.shape)
    modis_i, modis_j = np.unravel_index(indices, image_modis.latitude.shape)
    distance_mask = distance <= max_distance

    result = [((mersi_i[i], mersi_j[i]), (modis_i[i], modis_j[i])) for i in range(len(indices)) if distance_mask[i]]
    return result


def filter_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
        max_zenith_diff: int,
        max_zenith: int,
) -> list[tuple[int, int], tuple[int, int]]:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)

    has_no_clouds = image_modis.cloud_mask[*modis_pixels] == 3

    zenith_mersi = image_mersi.sensor_zenith[*mersi_pixels]
    zenith_modis = image_modis.sensor_zenith[*modis_pixels]
    zenith_diff_good = np.abs(zenith_modis - zenith_mersi) < max_zenith_diff
    zenith_not_big = zenith_mersi < max_zenith

    lon = image_mersi.longitude[*mersi_pixels]
    lat = image_mersi.latitude[*mersi_pixels]
    is_water = ~globe.is_land(lat, lon)

    mask = (
            has_no_clouds
            & zenith_diff_good
            & zenith_not_big
            & is_water
    )
    pixels = [pixels[i] for i in range(len(pixels)) if mask[i]]

    return pixels


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

    fig, ax = plt.subplots(ncols=2, nrows=2)
    ax[0][0].imshow(im1)
    ax[1][0].imshow(im2)
    ax[0][1].imshow(im3)
    ax[1][1].imshow(im4)

    ax[0][0].set_title("MERSI-2 image")
    ax[1][0].set_title("MERSI-2 matching pixels")
    ax[0][1].set_title("MODIS AQUA image")
    ax[1][1].set_title("MODIS AQUA matching pixels")
    plt.show()


def matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]]
) -> pd.DataFrame:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)
    mersi_rad = image_mersi.radiance[*mersi_pixels]
    modis_rad = image_modis.radiance[*modis_pixels]
    rad_diff = mersi_rad - modis_rad
    mersi_senz = image_mersi.sensor_zenith[*mersi_pixels]
    modis_senz = image_modis.sensor_zenith[*modis_pixels]
    mersi_counts = image_mersi.counts[*mersi_pixels]
    mersi_solz = image_mersi.solar_zenith[*mersi_pixels]
    modis_solz = image_modis.solar_zenith[*modis_pixels]

    df = pd.DataFrame({
        "mersi_rad": mersi_rad,
        "modis_rad": modis_rad,
        "rad_diff": rad_diff,
        "mersi_senz": mersi_senz,
        "modis_senz": modis_senz,
        "mersi_counts": mersi_counts,
        "mersi_solz": mersi_solz,
        "modis_solz": modis_solz,
    })
    print("Pixels in statistics:", len(df))
    return df


def save_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]]
) -> None:
    fmt = "%Y%m%d%H%M"
    filename = "{mersi_dt} {modis_dt}.pkl".format(
        mersi_dt=image_mersi.dt.strftime(fmt),
        modis_dt=image_modis.dt.strftime(fmt),
    )
    file_path = os.path.join(paths.MATCHING_PIXELS_DIR, filename)
    with open(file_path, "wb") as file:
        pickle.dump(pixels, file)


def load_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        force_recalculate=False,
) -> list[tuple[int, int], tuple[int, int]]:
    fmt = "%Y%m%d%H%M"
    filename = "{mersi_dt} {modis_dt}.pkl".format(
        mersi_dt=image_mersi.dt.strftime(fmt),
        modis_dt=image_modis.dt.strftime(fmt),
    )
    file_path = os.path.join(paths.MATCHING_PIXELS_DIR, filename)
    if os.path.exists(file_path) and not force_recalculate:
        with open(file_path, "rb") as file:
            return pickle.load(file)
    else:
        pixels = get_matching_pixels(image_mersi, image_modis)
        pixels = filter_matching_pixels(image_mersi, image_modis, pixels, max_zenith_diff=1000, max_zenith=2000)
        save_matching_pixels(image_mersi, image_modis, pixels)
        return pixels
