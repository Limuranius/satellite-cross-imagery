import os.path
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from global_land_mask import globe
import cv2

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
        use_cloud_mask: bool,
        use_land_mask: bool,
        use_water_pixels: bool,
        do_erosion: bool,
        correct_cloud_movement: bool,
) -> list[tuple[int, int], tuple[int, int]]:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)

    zenith_mersi = image_mersi.sensor_zenith[*mersi_pixels]
    zenith_modis = image_modis.sensor_zenith[*modis_pixels]
    zenith_diff_good = np.abs(zenith_modis - zenith_mersi) < max_zenith_diff
    zenith_not_big = zenith_mersi < max_zenith

    mask = zenith_diff_good & zenith_not_big
    if use_cloud_mask:
        has_no_clouds = image_modis.cloud_mask[*modis_pixels] == 3
        mask &= has_no_clouds
    if use_land_mask:
        lon = image_mersi.longitude[*mersi_pixels]
        lat = image_mersi.latitude[*mersi_pixels]
        is_water = ~globe.is_land(lat, lon)
        mask &= is_water
    if not use_water_pixels:
        mask &= ~image_modis.water_mask[*modis_pixels]
    if do_erosion:
        mask_mersi = np.zeros_like(image_mersi.radiance, dtype=bool)
        for i, ((mersi_i, mersi_j), (modis_i, modis_j)) in enumerate(pixels):
            mask_mersi[mersi_i, mersi_j] = mask[i]
        mask_mersi = mask_mersi.astype(np.uint8) * 255
        mask_mersi = cv2.erode(mask_mersi, np.ones((5, 5), dtype=np.uint8))
        for i, ((mersi_i, mersi_j), (modis_i, modis_j)) in enumerate(pixels):
            mask[i] = bool(mask_mersi[mersi_i, mersi_j])
    if correct_cloud_movement:
        cloud_mask = image_modis.cloud_mask == 0
        cloud_mask = cloud_mask.astype(np.uint8) * 255
        cloud_mask_dilated = cv2.dilate(cloud_mask, np.ones((9, 9), dtype=np.uint8))
        trace = cloud_mask_dilated ^ cloud_mask
        for i, ((mersi_i, mersi_j), (modis_i, modis_j)) in enumerate(pixels):
            mask[i] = mask[i] and not trace[modis_i, modis_j]

    pixels = [pixels[i] for i in range(len(pixels)) if mask[i]]

    return pixels


def visualize_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]]
):
    mask_mersi = np.zeros_like(image_mersi.radiance, dtype=bool)
    mask_modis = np.zeros_like(image_modis.radiance, dtype=bool)
    mersi_radiances = []
    modis_radiances = []
    for (mersi_i, mersi_j), (modis_i, modis_j) in pixels:
        mask_mersi[mersi_i, mersi_j] = True
        mask_modis[modis_i, modis_j] = True
        mersi_radiances.append(image_mersi.radiance[mersi_i, mersi_j])
        modis_radiances.append(image_modis.radiance[modis_i, modis_j])

    im1 = image_mersi.radiance.copy()
    im2 = image_mersi.radiance.copy()
    im2[~mask_mersi] = 0
    im3 = image_modis.radiance.copy()
    im4 = image_modis.radiance.copy()
    im4[~mask_modis] = 0

    fig, ax = plt.subplots(ncols=3, nrows=2)
    fig.set_figheight(15)
    fig.set_figwidth(30)
    ax[0][0].imshow(im1)
    ax[0][0].set_title("MERSI-2 image")

    ax[0][1].imshow(im2)
    ax[0][1].set_title("MERSI-2 matching pixels")

    ax[0][2].hist(mersi_radiances, bins=100)
    ax[0][2].set_title("MERSI-2 radiance histogram")
    ax[0][2].set_xlabel("radiance")

    ax[1][0].imshow(im3)
    ax[1][0].set_title("MODIS AQUA image")

    ax[1][1].imshow(im4)
    ax[1][1].set_title("MODIS AQUA matching pixels")

    ax[1][2].sharex(ax[0][2])
    ax[1][2].sharey(ax[0][2])
    ax[1][2].hist(modis_radiances, bins=100)
    ax[1][2].set_title("MODIS radiance histogram")
    ax[1][2].set_xlabel("radiance")



def matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
        filter_modis_overflow=True,
) -> pd.DataFrame:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)
    mersi_rad = image_mersi.radiance[*mersi_pixels]
    modis_rad = image_modis.radiance[*modis_pixels]
    rad_diff = mersi_rad - modis_rad
    mersi_senz = image_mersi.sensor_zenith[*mersi_pixels]
    modis_senz = image_modis.sensor_zenith[*modis_pixels]
    mersi_counts = image_mersi.counts[*mersi_pixels]
    modis_counts = image_modis.scaled_integers[*modis_pixels]
    mersi_solz = image_mersi.solar_zenith[*mersi_pixels]
    modis_solz = image_modis.solar_zenith[*modis_pixels]
    rad_relation = mersi_rad / modis_rad

    df = pd.DataFrame({
        "mersi_rad": mersi_rad,
        "modis_rad": modis_rad,
        "rad_diff": rad_diff,
        "mersi_senz": mersi_senz,
        "modis_senz": modis_senz,
        "mersi_counts": mersi_counts,
        "modis_counts": modis_counts,
        "mersi_solz": mersi_solz,
        "modis_solz": modis_solz,
        "rad_relation": rad_relation,
    })
    if filter_modis_overflow:
        # df = df[df["modis_counts"] != 65533]
        df = df[df["modis_counts"] < 60000]
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
        pixels = filter_matching_pixels(
            image_mersi,
            image_modis,
            pixels,
            max_zenith_diff=1500,
            max_zenith=3000,
            use_cloud_mask=False,
            use_land_mask=False,
            use_water_pixels=True,
            do_erosion=False,
            correct_cloud_movement=True,
        )
        save_matching_pixels(image_mersi, image_modis, pixels)
        return pixels
