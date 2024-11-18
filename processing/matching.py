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
from processing.std_map import load_rstd_map

# used in rstd filtering
KERNEL_SIZE = 5
RSTD_THRESHOLD = 0.02


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
) -> list[tuple[int, int], tuple[int, int]]:
    coords = np.array([image_mersi.longitude, image_mersi.latitude])
    coords = coords.transpose((1, 2, 0))
    coords = coords.reshape((-1, 2))  # flatten
    fast_match = image_modis.geo_kdtree.query(coords)
    distance, indices = fast_match

    max_distance = 0.01

    mersi_i, mersi_j = np.unravel_index(list(range(len(indices))), image_mersi.latitude.shape)
    modis_i, modis_j = np.unravel_index(indices, image_modis.latitude.shape)
    distance_mask = distance <= max_distance

    result = [((mersi_i[i], mersi_j[i]), (modis_i[i], modis_j[i])) for i in range(len(indices)) if distance_mask[i]]
    return result


def get_matching_pixels_filename(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        max_zenith_relative_diff: float,
        max_zenith: int,
        exclude_clouds: bool,
        exclude_land: bool,
        exclude_water: bool,
        do_erosion: bool,
        correct_cloud_movement: bool,
        use_rstd_filtering: bool,
        rstd_kernel_size: int,
        rstd_threshold: float,
        exclude_overflow: bool,
):
    dt_fmt = "%Y%m%d%H%M"
    filename = (f"mersi={image_mersi.dt.strftime(dt_fmt)} "
                f"modis={image_modis.dt.strftime(dt_fmt)} "
                f"band_mersi={image_mersi.band} "
                f"band_modis={image_modis.band} "
                f"zen_rel={max_zenith_relative_diff} "
                f"max_zen={max_zenith} "
                f"no_cloud={int(exclude_clouds)} "
                f"no_land={int(exclude_land)} "
                f"no_water={int(exclude_water)} "
                f"no_cloud_move={int(correct_cloud_movement)} "
                f"erosion={int(do_erosion)} "
                f"rstd_filt={int(use_rstd_filtering)} "
                f"rstd_kern={rstd_kernel_size} "
                f"rstd_thresh={rstd_threshold} "
                f"no_overflow={exclude_overflow}"
                ".pkl")
    file_path = os.path.join(paths.MATCHING_PIXELS_DIR, filename)
    return file_path


def filter_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
        max_zenith_relative_diff: float,
        max_zenith: int,
        exclude_clouds: bool,
        exclude_land: bool,
        exclude_water: bool,
        do_erosion: bool,
        correct_cloud_movement: bool,
        use_rstd_filtering: bool,
        rstd_kernel_size: int,
        rstd_threshold: float,
        exclude_overflow: bool,
) -> list[tuple[int, int], tuple[int, int]]:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)

    zenith_mersi = image_mersi.sensor_zenith[*mersi_pixels]
    zenith_modis = image_modis.sensor_zenith[*modis_pixels]
    # zenith_diff_good = np.abs(zenith_modis - zenith_mersi) < max_zenith_diff
    zenith_diff_good = np.abs(
        np.cos(np.radians(zenith_modis / 100)) / np.cos(np.radians(zenith_mersi / 100)) - 1) < max_zenith_relative_diff
    zenith_not_big = zenith_mersi < max_zenith

    mask = zenith_diff_good & zenith_not_big
    if exclude_clouds:
        has_no_clouds = image_modis.cloud_mask[*modis_pixels] == 3
        mask &= has_no_clouds
    if exclude_land:
        lon = image_mersi.longitude[*mersi_pixels]
        lat = image_mersi.latitude[*mersi_pixels]
        is_water = ~globe.is_land(lat, lon)
        mask &= is_water
    if exclude_water:
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
        cloud_mask = image_modis.cloud_mask != 3
        cloud_mask = cloud_mask.astype(np.uint8) * 255
        cloud_mask_dilated = cv2.dilate(cloud_mask, np.ones((5, 5), dtype=np.uint8))
        cloud_mask_eroded = cv2.erode(cloud_mask, np.ones((5, 5), dtype=np.uint8))
        trace = cloud_mask_dilated ^ cloud_mask_eroded
        for i, ((mersi_i, mersi_j), (modis_i, modis_j)) in enumerate(pixels):
            mask[i] = mask[i] and not trace[modis_i, modis_j]
    if use_rstd_filtering:
        mersi_std_map = load_rstd_map(image_mersi, rstd_kernel_size)
        for i, ((mersi_i, mersi_j), (modis_i, modis_j)) in enumerate(pixels):
            mask[i] = mask[i] and mersi_std_map[mersi_i, mersi_j] < rstd_threshold
    if exclude_overflow:
        for i, (mersi_coord, modis_coord) in enumerate(pixels):
            mersi_overflow = image_mersi.counts[*mersi_coord] > 4050
            modis_overflow = image_modis.scaled_integers[*modis_coord] > 60000
            mask[i] = mask[i] and not mersi_overflow and not modis_overflow

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
    ax[0][1].sharex(ax[0][0])
    ax[0][1].sharey(ax[0][0])

    ax[0][2].hist(mersi_radiances, bins=100)
    ax[0][2].set_title("MERSI-2 matching pixels radiance histogram")
    ax[0][2].set_xlabel("radiance")

    ax[1][0].imshow(im3)
    ax[1][0].set_title("MODIS AQUA image")

    ax[1][1].imshow(im4)
    ax[1][1].set_title("MODIS AQUA matching pixels")
    ax[1][0].sharex(ax[1][1])
    ax[1][0].sharey(ax[1][1])

    ax[1][2].sharex(ax[0][2])
    ax[1][2].sharey(ax[0][2])
    ax[1][2].hist(modis_radiances, bins=100)
    ax[1][2].set_title("MODIS matching pixels radiance histogram")
    ax[1][2].set_xlabel("radiance")


def matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
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
    mersi_y = modis_pixels[0]

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
        "mersi_y": mersi_y,
    })
    print("Pixels in statistics:", len(df))
    return df


def aggregated_matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
) -> pd.DataFrame:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)

    df = pd.DataFrame(columns=[
        "mersi_rad",
        "modis_rad",
        "rad_relation",
        "mersi_count",
    ], index=range(len(pixels)))
    df_i = 0

    mersi_visited_mask = np.zeros(shape=(2000, 2048), dtype=bool)
    indices = np.full(shape=(2000, 2048), fill_value=-1, dtype=int)
    indices[*mersi_pixels] = np.arange(len(pixels))

    for mersi_pixel, modis_pixel in tqdm.tqdm(pixels, desc="Aggregating statistics"):
        if not mersi_visited_mask[*mersi_pixel]:
            mersi_i, mersi_j = mersi_pixel

            indices_window = indices[
                             mersi_i - KERNEL_SIZE // 2: mersi_i + KERNEL_SIZE // 2 + 1,
                             mersi_j - KERNEL_SIZE // 2: mersi_j + KERNEL_SIZE // 2 + 1
                             ]

            window_pixel_indices = indices_window[indices_window != -1]

            window_mersi_pixels = mersi_pixels[:, window_pixel_indices]
            window_modis_pixels = modis_pixels[:, window_pixel_indices]

            mersi_visited_mask[*window_mersi_pixels] = True

            window_mersi_rad = image_mersi.radiance[*window_mersi_pixels]
            window_modis_rad = image_modis.radiance[*window_modis_pixels]
            window_mersi_rad_mean = window_mersi_rad.mean()
            window_modis_rad_mean = window_modis_rad.mean()
            rad_relation = window_mersi_rad_mean / window_modis_rad_mean
            window_mersi_count = image_mersi.counts[*window_mersi_pixels].mean()

            # Filtering windows by rstd
            mersi_rstd = window_mersi_rad.std() / window_mersi_rad.mean()
            modis_rstd = window_modis_rad.std() / window_modis_rad.mean()
            if (mersi_rstd + modis_rstd) / 2 > 0.05:
                continue

            df.loc[df_i] = [window_mersi_rad_mean, window_modis_rad_mean, rad_relation, window_mersi_count]
            df_i += 1
    df = df.iloc[0: df_i]

    print("Pixels in statistics:", len(df))
    return df


def load_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,

        max_zenith_relative_diff: float,
        max_zenith: int,
        exclude_clouds: bool,
        exclude_land: bool,
        exclude_water: bool,
        do_erosion: bool,
        correct_cloud_movement: bool,
        use_rstd_filtering: bool,
        rstd_kernel_size: int = KERNEL_SIZE,
        rstd_threshold: float = RSTD_THRESHOLD,

        exclude_overflow: bool = True,

        force_recalculate=False,
) -> list[tuple[int, int], tuple[int, int]]:
    file_path = get_matching_pixels_filename(
        image_mersi, image_modis,
        max_zenith_relative_diff, max_zenith,
        exclude_clouds, exclude_land, exclude_water,
        do_erosion, correct_cloud_movement,
        use_rstd_filtering, rstd_kernel_size, rstd_threshold,
        exclude_overflow,
    )
    if os.path.exists(file_path) and not force_recalculate:
        with open(file_path, "rb") as file:
            return pickle.load(file)
    else:
        print("Matching pixels... ", end="")
        pixels = get_matching_pixels(image_mersi, image_modis)
        pixels = filter_matching_pixels(
            image_mersi, image_modis, pixels,
            max_zenith_relative_diff, max_zenith,
            exclude_clouds, exclude_land, exclude_water,
            do_erosion, correct_cloud_movement,
            use_rstd_filtering, rstd_kernel_size, rstd_threshold,
            exclude_overflow
        )
        print("Done!")
        with open(file_path, "wb") as file:
            pickle.dump(pixels, file)
        return pixels
