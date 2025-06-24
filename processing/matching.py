import os.path
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from global_land_mask import globe
import cv2

import paths
from custom_types import MatchingPixelsArray
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.std_map import load_rstd_map


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
) -> MatchingPixelsArray:
    coords = np.array([image_mersi.longitude, image_mersi.latitude])
    coords = coords.transpose((1, 2, 0))
    coords = coords.reshape((-1, 2))  # flatten
    if not hasattr(image_modis, "geo_kdtree"):
        image_modis.create_kdtree()
    fast_match = image_modis.geo_kdtree.query(coords)
    distance, indices = fast_match

    max_distance = 0.01

    mersi_i, mersi_j = np.unravel_index(list(range(len(indices))), image_mersi.latitude.shape)
    modis_i, modis_j = np.unravel_index(indices, list(image_modis.counts.shape))
    distance_mask = distance <= max_distance

    result = np.array([
        [mersi_i, mersi_j],
        [modis_i, modis_j],
    ]).transpose((2, 0, 1))
    result = result[distance_mask]
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
        pixels: MatchingPixelsArray,
        max_zenith_relative_diff: float = None,
        max_zenith: int = None,
        exclude_clouds: bool = False,
        exclude_land: bool = False,
        exclude_water: bool = False,
        do_erosion: bool = False,
        correct_cloud_movement: bool = False,
        use_rstd_filtering: bool = False,
        rstd_kernel_size: int = 5,
        rstd_threshold: float = 0.1,
        exclude_overflow: bool = False,
        remove_glint: bool = False,
        use_clear_sea: bool = False,
        remove61: bool = False,
        erosion_size = 5,
) -> MatchingPixelsArray:
    mersi_pixels = pixels[:, 0].transpose(1, 0)
    modis_pixels = pixels[:, 1].transpose(1, 0)
    mask = np.ones(len(pixels), dtype=bool)

    zenith_mersi = image_mersi.sensor_zenith[*mersi_pixels]
    zenith_modis = image_modis.sensor_zenith[*modis_pixels]

    if max_zenith_relative_diff:
        zenith_diff_good = np.abs(
            np.cos(np.radians(zenith_modis / 100)) /
            np.cos(np.radians(zenith_mersi / 100)) - 1
        ) < max_zenith_relative_diff
        mask &= zenith_diff_good

    if max_zenith:
        mersi_zenith_not_big = zenith_mersi < max_zenith
        modis_zenith_not_big = zenith_modis < max_zenith
        mask &= mersi_zenith_not_big & modis_zenith_not_big

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
        mask_mersi = cv2.erode(mask_mersi, np.ones((erosion_size, erosion_size), dtype=np.uint8))
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
            modis_overflow = image_modis.counts[*modis_coord] > 60000
            mask[i] = mask[i] and not mersi_overflow and not modis_overflow
    if remove_glint:
        try:
            clm = image_mersi.cloud_mask()
            # clear_sea_mask = image_mersi.cloud_mask() == 63
            # not_glint_mask = image_mersi.cloud_mask() != 47
            # not_glint_mask = ~np.isin(image_mersi.cloud_mask(), [45, 43, 41])
            not_glint_mask = (clm & 16) != 0
            for i, (mersi_coord, modis_coord) in enumerate(pixels):
                mask[i] = mask[i] and not_glint_mask[*mersi_coord]
        except:
            print(f"Error: CLM not found. {image_mersi.dt}")
            mask &= False
    if use_clear_sea:
        try:
            clear_sea_mask = image_mersi.cloud_mask() == 63
            mask &= clear_sea_mask[*mersi_pixels]
        except:
            print(f"Error: CLM not found. {image_mersi.dt}")
            mask &= False
    if remove61:
        try:
            clm = image_mersi.cloud_mask()
            mask61 = clm != 61
            for i, (mersi_coord, modis_coord) in enumerate(pixels):
                mask[i] = mask[i] and mask61[*mersi_coord]
        except:
            print(f"Error: CLM not found. {image_mersi.dt}")
            mask &= False
    pixels = pixels[mask]
    return pixels


def matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
) -> pd.DataFrame:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)
    mersi_rad = image_mersi.radiance[*mersi_pixels]
    modis_rad = image_modis.radiance[*modis_pixels]
    mersi_ref = image_mersi.reflectance[*mersi_pixels]
    modis_ref = image_modis.reflectance[*modis_pixels]
    mersi_senz = image_mersi.sensor_zenith[*mersi_pixels]
    modis_senz = image_modis.sensor_zenith[*modis_pixels]
    mersi_sena = image_mersi.sensor_azimuth[*mersi_pixels]
    modis_sena = image_modis.sensor_azimuth[*modis_pixels]
    mersi_counts = image_mersi.counts[*mersi_pixels]
    modis_counts = image_modis.counts[*modis_pixels]
    mersi_solz = image_mersi.solar_zenith[*mersi_pixels]
    modis_solz = image_modis.solar_zenith[*modis_pixels]
    mersi_sola = image_mersi.solar_azimuth[*mersi_pixels]
    modis_sola = image_modis.solar_azimuth[*modis_pixels]
    mersi_y = mersi_pixels[0]
    sensor = mersi_y % 10

    df = pd.DataFrame({
        "mersi_rad": mersi_rad,
        "modis_rad": modis_rad,
        "mersi_ref": mersi_ref,
        "modis_ref": modis_ref,
        "mersi_senz": mersi_senz,
        "modis_senz": modis_senz,
        "mersi_counts": mersi_counts,
        "modis_counts": modis_counts,
        "mersi_solz": mersi_solz,
        "modis_solz": modis_solz,
        "mersi_y": mersi_y,
        "sensor": sensor,
        "mersi_sena": mersi_sena,
        "modis_sena": modis_sena,
        "mersi_sola": mersi_sola,
        "modis_sola": modis_sola,
    })
    # print("Pixels in statistics:", len(df))
    return df


def aggregated_matching_stats(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        pixels: list[tuple[int, int], tuple[int, int]],
        kernel_size: int,
) -> pd.DataFrame:
    mersi_pixels = np.array([pixel[0] for pixel in pixels]).transpose(1, 0)
    modis_pixels = np.array([pixel[1] for pixel in pixels]).transpose(1, 0)

    df = pd.DataFrame(columns=[
        "mersi_rad",
        "modis_rad",
        "mersi_count",
        "mersi_senz",
        "modis_senz",
    ], index=range(len(pixels)))
    df_i = 0

    mersi_visited_mask = np.zeros(shape=(2000, 2048), dtype=bool)
    indices = np.full(shape=(2000, 2048), fill_value=-1, dtype=int)
    indices[*mersi_pixels] = np.arange(len(pixels))
    mersi_radiance = image_mersi.radiance
    mersi_senz = image_mersi.sensor_zenith
    modis_senz = image_modis.sensor_zenith
    for mersi_pixel, modis_pixel in tqdm.tqdm(pixels, desc="Aggregating statistics"):
        if not mersi_visited_mask[*mersi_pixel]:
            mersi_i, mersi_j = mersi_pixel
            indices_window = indices[
                             mersi_i - kernel_size // 2: mersi_i + kernel_size // 2 + 1,
                             mersi_j - kernel_size // 2: mersi_j + kernel_size // 2 + 1
                             ]
            # print(indices_window)

            window_pixel_indices = indices_window[indices_window != -1]

            window_mersi_pixels = mersi_pixels[:, window_pixel_indices]
            window_modis_pixels = modis_pixels[:, window_pixel_indices]

            mersi_visited_mask[*window_mersi_pixels] = True

            window_mersi_rad = mersi_radiance[*window_mersi_pixels]
            window_modis_rad = image_modis.radiance[*window_modis_pixels]
            window_mersi_rad_mean = window_mersi_rad.mean()
            window_modis_rad_mean = window_modis_rad.mean()
            window_mersi_count = image_mersi.counts[*window_mersi_pixels].mean()

            # # Filtering windows by rstd
            # mersi_rstd = window_mersi_rad.std() / window_mersi_rad.mean()
            # modis_rstd = window_modis_rad.std() / window_modis_rad.mean()
            # if (mersi_rstd + modis_rstd) / 2 > 0.05:
            #     continue

            df.loc[df_i] = [
                window_mersi_rad_mean,
                window_modis_rad_mean,
                window_mersi_count,
                mersi_senz[*window_mersi_pixels].mean(),
                modis_senz[*window_modis_pixels].mean(),
            ]
            df_i += 1
    df = df.iloc[0: df_i]

    df["mersi_rad"] = df["mersi_rad"].astype(float)
    df["modis_rad"] = df["modis_rad"].astype(float)
    df["mersi_count"] = df["mersi_count"].astype(float)

    print("Pixels in statistics:", len(df))
    return df

